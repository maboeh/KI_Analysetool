"""
PDF-Report-Generator für das KI Analysetool.

Erstellt vollständige Analyse-Reports mit Deckblatt, Inhaltsverzeichnis,
Detailanalyse, extrahierten Daten (als Tabellen) und eingebetteten
Visualisierungen.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Image as RLImage, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas

from data_models import ProcessedResult


class _NumberedDocTemplate(SimpleDocTemplate):
    """SimpleDocTemplate mit automatischer Inhaltsverzeichnis-Erfassung."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = []

    def afterFlowable(self, flowable):
        """Erfasst Überschriften für das Inhaltsverzeichnis."""
        if hasattr(flowable, "getPlainText"):
            text = flowable.getPlainText()
            style_name = flowable.style.name
            if style_name == "Heading1":
                self.notify("TOCEntry", (0, text, self.page))
            elif style_name == "Heading2":
                self.notify("TOCEntry", (1, text, self.page))


class PDFReportGenerator:
    """Generiert vollständige PDF-Reports aus ProcessedResult-Objekten."""

    def __init__(self):
        self.styles = self._create_styles()

    def _create_styles(self):
        """Erstellt die Paragraph-Styles für den Report."""
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor("#1a3a5c"),
        ))
        styles.add(ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["Normal"],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#444444"),
            spaceAfter=10,
        ))
        styles.add(ParagraphStyle(
            name="ReportBody",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ))
        return styles

    def generate_report(self, result: ProcessedResult,
                        output_path: Optional[str] = None,
                        include_charts: bool = True,
                        include_data_tables: bool = True) -> str:
        """
        Generiert einen vollständigen PDF-Report.

        Args:
            result: Das ProcessedResult mit Analyse-Inhalt und Daten.
            output_path: Optionaler Pfad; sonst Dialog oder Standard-Name.
            include_charts: Ob Visualisierungen eingebettet werden.
            include_data_tables: Ob extrahierte Daten als Tabellen eingebettet werden.

        Returns:
            Pfad zur erstellten PDF-Datei.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join("exports", f"analyse_report_{timestamp}.pdf")

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        doc = _NumberedDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2 * cm,
            title="KI Analysetool - Report",
            author="KI Analysetool",
        )

        story = []

        # --- Deckblatt ---
        story.extend(self._build_cover_page(result))
        story.append(PageBreak())

        # --- Inhaltsverzeichnis ---
        story.extend(self._build_table_of_contents())
        story.append(PageBreak())

        # --- Hauptinhalt: Detailanalyse ---
        story.extend(self._build_analysis_section(result))

        # --- Extrahierte Daten ---
        if include_data_tables and result.extracted_data:
            story.extend(self._build_data_section(result))

        # --- Visualisierungen ---
        if include_charts and result.visualizations:
            story.extend(self._build_charts_section(result))

        # --- Anhang: Metadaten & Quellen ---
        story.extend(self._build_appendix(result))

        # Dokument bauen (zweimal für TOC)
        doc.multiBuild(story)

        logging.info(f"PDF-Report erstellt: {output_path}")
        return output_path

    # --- Sektionen ---

    def _build_cover_page(self, result: ProcessedResult):
        elements = []
        elements.append(Spacer(1, 5 * cm))
        elements.append(Paragraph("KI Analysetool", self.styles["CoverTitle"]))
        elements.append(Spacer(1, 1 * cm))
        elements.append(Paragraph("Analyse-Report", self.styles["CoverSubtitle"]))
        elements.append(Spacer(1, 3 * cm))

        # Metadaten auf dem Deckblatt
        meta_lines = [
            f"<b>Erstellt am:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            f"<b>Analysetyp:</b> {xml_escape(result.metadata.analysis_type)}",
            f"<b>Modell:</b> {xml_escape(result.metadata.model_used or '—')}",
        ]
        if result.source_info:
            source = (result.source_info.file_name
                      or result.source_info.url
                      or result.source_info.file_path
                      or "—")
            meta_lines.append(f"<b>Quelle:</b> {xml_escape(source)}")
        if result.metadata.tags:
            meta_lines.append(f"<b>Tags:</b> {xml_escape(', '.join(result.metadata.tags))}")

        for line in meta_lines:
            elements.append(Paragraph(line, self.styles["CoverSubtitle"]))
            elements.append(Spacer(1, 4 * mm))

        return elements

    def _build_table_of_contents(self):
        elements = []
        elements.append(Paragraph("Inhaltsverzeichnis", self.styles["Heading1"]))
        elements.append(Spacer(1, 0.5 * cm))
        toc = TableOfContents()
        toc.levelStyles = [
            ParagraphStyle(name="TOC1", fontSize=12, leftIndent=0, spaceBefore=4),
            ParagraphStyle(name="TOC2", fontSize=10, leftIndent=20, spaceBefore=2),
        ]
        elements.append(toc)
        return elements

    def _build_analysis_section(self, result: ProcessedResult):
        elements = []
        elements.append(Paragraph("Detailanalyse", self.styles["Heading1"]))
        elements.append(Spacer(1, 0.3 * cm))

        # Inhalt als Paragraphs (Markdown-ähnlich → einfache Umwandlung)
        content = result.content or "(Kein Inhalt vorhanden)"
        for paragraph_text in self._split_into_paragraphs(content):
            safe = xml_escape(paragraph_text).replace("\n", "<br/>")
            elements.append(Paragraph(safe, self.styles["ReportBody"]))

        return elements

    def _build_data_section(self, result: ProcessedResult):
        elements = []
        data = result.extracted_data

        # Tabellen
        if data.tables:
            elements.append(Paragraph("Extrahierte Tabellen", self.styles["Heading1"]))
            for i, table in enumerate(data.tables, 1):
                elements.append(Paragraph(
                    f"Tabelle {i}: {xml_escape(table.title or 'Ohne Titel')}",
                    self.styles["Heading2"]
                ))
                elements.append(self._render_table(table))
                elements.append(Spacer(1, 0.5 * cm))

        # Entitäten
        if data.entities:
            elements.append(Paragraph("Erkannte Entitäten", self.styles["Heading1"]))
            elements.append(self._render_entities_table(data.entities))
            elements.append(Spacer(1, 0.5 * cm))

        # Numerische Werte
        if data.numeric_values:
            elements.append(Paragraph("Numerische Werte", self.styles["Heading1"]))
            elements.append(self._render_numeric_table(data.numeric_values))

        return elements

    def _build_charts_section(self, result: ProcessedResult):
        elements = []
        elements.append(Paragraph("Visualisierungen", self.styles["Heading1"]))
        for i, viz in enumerate(result.visualizations, 1):
            elements.append(Paragraph(
                f"Diagramm {i}: {xml_escape(viz.title or 'Ohne Titel')}",
                self.styles["Heading2"]
            ))
            if viz.file_path and os.path.exists(viz.file_path):
                try:
                    img = RLImage(viz.file_path, width=15 * cm, height=10 * cm)
                    img.hAlign = "CENTER"
                    elements.append(KeepTogether([img, Spacer(1, 0.5 * cm)]))
                except Exception as e:
                    elements.append(Paragraph(
                        f"<i>Diagramm konnte nicht eingebettet werden: {xml_escape(str(e))}</i>",
                        self.styles["ReportBody"]
                    ))
            else:
                elements.append(Paragraph(
                    "<i>Diagramm-Datei nicht verfügbar.</i>",
                    self.styles["ReportBody"]
                ))
        return elements

    def _build_appendix(self, result: ProcessedResult):
        elements = []
        elements.append(Paragraph("Anhang", self.styles["Heading1"]))

        # Metadaten-Tabelle
        meta_rows = [
            ["Erstellt am", result.created_at.strftime("%d.%m.%Y %H:%M")],
            ["Analysetyp", result.metadata.analysis_type],
            ["Modell", result.metadata.model_used or "—"],
            ["Verarbeitungszeit", f"{result.metadata.processing_time or 0:.2f}s"],
            ["Tokens", str(result.metadata.tokens_used or 0)],
        ]
        if result.source_info:
            meta_rows.append(["Quelltyp", result.source_info.type or "—"])
            meta_rows.append(["Quelle", result.source_info.file_name or result.source_info.url or "—"])

        meta_table = Table(meta_rows, colWidths=[5 * cm, 11 * cm])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eef5")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(Paragraph("Metadaten", self.styles["Heading2"]))
        elements.append(meta_table)

        # Methodik-Hinweis
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("Methodik", self.styles["Heading2"]))
        elements.append(Paragraph(
            "Dieser Report wurde mit dem KI Analysetool erstellt. Die Analyse "
            "erfolgte mittels OpenAI GPT-Modellen. Extrahierte Daten und "
            "Visualisierungen wurden automatisch generiert und sollten vor "
            "weiterführenden Schlussfolgerungen validiert werden.",
            self.styles["ReportBody"]
        ))

        return elements

    # --- Hilfsmethoden ---

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Teilt Text in Absätze (anhand von Leerzeilen)."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()] if text.strip() else [""]
        return paragraphs

    def _render_table(self, data_table) -> Table:
        """Rendert ein DataTable-Objekt als ReportLab-Tabelle."""
        headers = data_table.headers or []
        rows = data_table.rows or []

        table_data = [headers] + rows
        # XML-Escaping aller Zellen
        table_data = [[xml_escape(str(cell)) for cell in row] for row in table_data]

        rl_table = Table(table_data, repeatRows=1)
        rl_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f0f4f8")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return rl_table

    def _render_entities_table(self, entities) -> Table:
        """Rendert Entitäten als Tabelle."""
        table_data = [["Typ", "Text", "Konfidenz"]]
        for ent in entities:
            table_data.append([
                xml_escape(ent.entity_type.value if hasattr(ent.entity_type, "value") else str(ent.entity_type)),
                xml_escape(getattr(ent, "text", "") or ""),
                f"{ent.confidence:.2f}" if hasattr(ent, "confidence") and ent.confidence else "",
            ])
        rl_table = Table(table_data, repeatRows=1, colWidths=[3 * cm, 6 * cm, 7 * cm])
        rl_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f0f4f8")]),
        ]))
        return rl_table

    def _render_numeric_table(self, numeric_values) -> Table:
        """Rendert numerische Werte als Tabelle."""
        table_data = [["Wert", "Typ", "Kontext"]]
        for nv in numeric_values:
            table_data.append([
                xml_escape(str(nv.value)),
                xml_escape(nv.value_type or ""),
                xml_escape(nv.context or ""),
            ])
        rl_table = Table(table_data, repeatRows=1, colWidths=[4 * cm, 4 * cm, 8 * cm])
        rl_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f0f4f8")]),
        ]))
        return rl_table
