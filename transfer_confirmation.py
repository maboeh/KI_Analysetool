"""Kombinierte Bestätigung vor der Übertragung an einen externen KI-Anbieter.

Vor jedem Request an OpenAI (oder einen anderen externen Provider) wird der
ausgehende Inhalt lokal auf personenbezogene Daten und Secrets geprüft. Bei
Funden, sensiblen Quellen (z. B. PDF-Upload) oder Budget-Warnungen zeigt
`confirm_transfer` einen Dialog mit drei Optionen: senden, schwärzen &
senden oder abbrechen.

Die Dialog-Entscheidung ist vom UI entkoppelt: `evaluate_transfer` liefert
alle nötigen Informationen, `confirm_transfer` rendert sie nur bei Bedarf.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from analysis import estimate_request_cost, get_budget_status
from privacy_scanner import PrivacyReport, redact_text, scan_text

logger = logging.getLogger(__name__)


TRANSFER_NOTICES = {
    "pdf": "Die PDF-Datei wird zu OpenAI hochgeladen und dort verarbeitet.",
    "website": "Der extrahierte Inhalt der Webseite wird an OpenAI übertragen.",
    "youtube": "Das extrahierte YouTube-Transkript wird an OpenAI übertragen.",
    "image": "Der per OCR extrahierte Text des Bildes wird an OpenAI übertragen.",
    "file": "Der extrahierte Dateiinhalt wird an OpenAI übertragen.",
    "default": "Der Inhalt wird zur Analyse an OpenAI übertragen.",
}

# Quellen, bei denen immer ein expliziter Hinweis gezeigt wird, weil die
# Originaldatei (nicht nur Text) das Gerät verlässt.
_ALWAYS_NOTIFY_SOURCES = frozenset({"pdf"})


@dataclass(frozen=True)
class TransferContext:
    """Alle Informationen, die für die Bestätigungsentscheidung nötig sind."""

    content: str
    source_type: str
    notice: str
    report: PrivacyReport
    estimated_cost: float
    estimated_input_tokens: int
    budget: dict
    external: bool = True
    model_warning: Optional[str] = None

    @property
    def needs_confirmation(self) -> bool:
        """Dialog nötig bei Funden, sensiblen Quellen, Budget- oder
        Modell-Warnung."""
        return (
            self.report.has_findings
            or (self.external and self.source_type in _ALWAYS_NOTIFY_SOURCES)
            or self.budget.get("warning", False)
            or self.budget.get("projected_warning", False)
            or self.model_warning is not None
        )


@dataclass(frozen=True)
class TransferDecision:
    """Ergebnis der Bestätigung."""

    proceed: bool
    content: str
    redacted: bool = False


def evaluate_transfer(content: str, source_type: str = "default",
                      privacy_check: bool = True) -> TransferContext:
    """Bewertet einen ausgehenden Inhalt ohne UI – rein lokal.

    Args:
        content: Der vollständige an den Provider gehende Text.
        source_type: Quelltyp (pdf, website, youtube, image, default ...).
        privacy_check: Wenn False, wird der PII-Scan übersprungen.
    """
    from analysis import get_provider, is_local_provider
    provider = get_provider()
    local = is_local_provider()

    report = scan_text(content) if privacy_check else PrivacyReport(findings=[])
    estimate = estimate_request_cost(content)
    budget = get_budget_status()
    if budget.get("limit"):
        projected = (budget["spent"] + estimate["estimated_cost"]) / budget["limit"]
        budget = {
            **budget,
            "projected_fraction": round(projected, 3),
            "projected_warning": projected >= 0.8,
            "projected_exceeded": projected >= 1.0,
        }
    model_warning = None
    if local:
        provider_name = provider.name if provider else "lokaler Server"
        notice = (f"Der Inhalt wird lokal verarbeitet ({provider_name}). "
                  "Es findet keine Übertragung an einen Cloud-Anbieter statt.")
        from analysis import _default_session
        from providers import looks_like_cloud_model
        if looks_like_cloud_model(_default_session.current_model):
            model_warning = (
                f"Das Modell '{_default_session.current_model}' sieht wie ein "
                "OpenAI-Cloud-Modell aus und ist auf dem lokalen Server "
                "vermutlich nicht installiert. Lokale Server benötigen lokal "
                "installierte Modellnamen (z. B. 'llama3:latest') – die "
                "Anfrage wird wahrscheinlich fehlschlagen. Es werden "
                "trotzdem keine Daten an einen Cloud-Anbieter gesendet.")
    else:
        notice = TRANSFER_NOTICES.get(source_type, TRANSFER_NOTICES["default"])
    return TransferContext(
        content=content,
        source_type=source_type,
        notice=notice,
        report=report,
        estimated_cost=estimate["estimated_cost"],
        estimated_input_tokens=estimate["input_tokens"],
        budget=budget,
        external=not local,
        model_warning=model_warning,
    )


def confirm_transfer(parent, content: str, source_type: str = "default",
                     privacy_check: bool = True) -> TransferDecision:
    """Prüft den Inhalt und zeigt bei Bedarf den kombinierten Dialog.

    Args:
        parent: Übergeordnetes Tk-Fenster.
        content: Vollständiger ausgehender Text.
        source_type: Quelltyp für den Übertragungshinweis.
        privacy_check: PII-Scan aktivieren/deaktivieren.

    Returns:
        TransferDecision; proceed=False bedeutet Abbruch durch den Nutzer.
    """
    context = evaluate_transfer(content, source_type, privacy_check)
    if not context.needs_confirmation:
        return TransferDecision(proceed=True, content=content)
    return _show_confirmation_dialog(parent, context)


def _show_confirmation_dialog(parent, context: TransferContext) -> TransferDecision:
    """Modaler Dialog: Übertragungshinweis + Funde + Kosten + Budget."""
    import tkinter as tk
    from tkinter import ttk

    result = {"proceed": False, "redacted": False}

    dialog = tk.Toplevel(parent)
    dialog.title("Datenübertragung" if context.external
                 else "Lokale Verarbeitung")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)

    frame = ttk.Frame(dialog, padding=15)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Vor dem Senden prüfen",
              font=("Segoe UI", 12, "bold")).pack(anchor=tk.W)

    ttk.Label(frame, text=context.notice, wraplength=440,
              justify=tk.LEFT).pack(anchor=tk.W, pady=(8, 0))

    if context.model_warning:
        ttk.Label(
            frame, text=f"Warnung: {context.model_warning}",
            wraplength=440, justify=tk.LEFT,
            foreground="#a06000",
        ).pack(anchor=tk.W, pady=(8, 0))

    if context.report.has_findings:
        counts = context.report.count_by_kind()
        ttk.Label(
            frame,
            text="Lokal erkannte sensible Daten:",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=tk.W, pady=(10, 2))
        for finding in context.report.findings[:10]:
            ttk.Label(
                frame,
                text=f"• {finding.label}: {finding.masked_preview}",
                wraplength=440,
            ).pack(anchor=tk.W, padx=10)
        extra = sum(counts.values()) - min(10, sum(counts.values()))
        if extra > 0:
            ttk.Label(frame, text=f"… und {extra} weitere Fundstelle(n)."
                      ).pack(anchor=tk.W, padx=10)
        ttk.Label(
            frame,
            text="Empfehlung: 'Schwärzen & senden' ersetzt die Funde durch Platzhalter.",
            wraplength=440, justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(4, 0))

    budget = context.budget
    if budget.get("limit"):
        budget_text = (
            f"Sitzungsbudget: ${budget['spent']:.4f} von ${budget['limit']:.4f} "
            f"verbraucht"
        )
        if budget.get("projected_exceeded") or budget.get("exceeded"):
            budget_text += " — Budget wird überschritten!"
        elif budget.get("projected_warning") or budget.get("warning"):
            budget_text += " — über 80 % verbraucht"
        ttk.Label(frame, text=budget_text, wraplength=440,
                  justify=tk.LEFT).pack(anchor=tk.W, pady=(10, 0))

    ttk.Label(
        frame,
        text=(f"Geschätzte Kosten dieser Anfrage: ~${context.estimated_cost:.4f} "
              f"(~{context.estimated_input_tokens:,} Eingabe-Tokens)"),
        wraplength=440, justify=tk.LEFT,
    ).pack(anchor=tk.W, pady=(8, 0))

    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, pady=(15, 0))

    def choose(proceed: bool, redacted: bool):
        result["proceed"] = proceed
        result["redacted"] = redacted
        dialog.destroy()

    send_button = ttk.Button(button_frame, text="Senden",
                             command=lambda: choose(True, False))
    send_button.pack(side=tk.LEFT)

    if context.report.has_findings:
        ttk.Button(button_frame, text="Schwärzen & senden",
                   command=lambda: choose(True, True)).pack(side=tk.LEFT, padx=8)

    ttk.Button(button_frame, text="Abbrechen",
               command=lambda: choose(False, False)).pack(side=tk.RIGHT)

    send_button.focus_set()
    dialog.bind("<Escape>", lambda _event: choose(False, False))
    dialog.protocol("WM_DELETE_WINDOW", lambda: choose(False, False))
    dialog.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - dialog.winfo_width()) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - dialog.winfo_height()) // 2)
    dialog.geometry(f"+{x}+{y}")
    dialog.wait_window()

    if not result["proceed"]:
        logger.info("Übertragung vom Nutzer abgebrochen (%s).", context.source_type)
        return TransferDecision(proceed=False, content=context.content)

    if result["redacted"]:
        redacted_content = redact_text(context.content, context.report)
        logger.info("Übertragung mit %d geschwärzten Fundstellen bestätigt.",
                    len(context.report.findings))
        return TransferDecision(proceed=True, content=redacted_content, redacted=True)

    return TransferDecision(proceed=True, content=context.content)
