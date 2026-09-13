"""
Results Manager for storing and retrieving processed analysis results.

This module provides the ResultsManager class which handles persistent storage
of ProcessedResult objects using SQLite for metadata and JSON for content.
"""

import sqlite3
import json
import os
import uuid
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from data_models import ProcessedResult, ResultSummary, SourceInfo, ResultMetadata


class ResultsManager:
    """Manages storage and retrieval of processed analysis results."""
    
    def __init__(self, db_path: str = "results.db", results_dir: str = "results"):
        """
        Initialize the ResultsManager.
        
        Args:
            db_path: Path to SQLite database file
            results_dir: Directory to store result JSON files
        """
        self.db_path = db_path
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialisiert das Schema über das versionierte Migrationsframework."""
        from migrations import migrate
        migrate(self.db_path)
    
    def save_result(self, result: ProcessedResult, name: Optional[str] = None) -> str:
        """
        Save a ProcessedResult to persistent storage.
        
        Args:
            result: The ProcessedResult to save
            name: Optional custom name for the result
            
        Returns:
            The ID of the saved result
        """
        # Generate title if not provided
        if name is None:
            name = self._generate_title(result)
        
        # Save JSON content to file
        json_file_path = self.results_dir / f"{result.id}.json"
        temporary_json_path = self.results_dir / f".{result.id}.json.tmp"
        with open(temporary_json_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # Save metadata to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO results (
                        id, title, analysis_type, source_type, source_url,
                        source_file_path, source_file_name, content_preview,
                        has_visualizations, has_exportable_data, processing_time,
                        model_used, tokens_used, confidence_score, tags,
                        created_at, updated_at, json_file_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.id,
                    name,
                    result.metadata.analysis_type,
                    result.source_info.type if result.source_info else None,
                    result.source_info.url if result.source_info else None,
                    result.source_info.file_path if result.source_info else None,
                    result.source_info.file_name if result.source_info else None,
                    result.content[:500] + "..." if len(result.content) > 500 else result.content,
                    len(result.visualizations) > 0,
                    result.has_exportable_data(),
                    result.metadata.processing_time,
                    result.metadata.model_used,
                    result.metadata.tokens_used,
                    result.metadata.confidence_score,
                    json.dumps(result.metadata.tags),
                    result.created_at.isoformat(),
                    result.updated_at.isoformat(),
                    str(json_file_path)
                ))
                os.replace(temporary_json_path, json_file_path)
                conn.commit()
        finally:
            if temporary_json_path.exists():
                temporary_json_path.unlink()

        return result.id
    
    def load_result(self, result_id: str) -> Optional[ProcessedResult]:
        """
        Load a ProcessedResult by ID.
        
        Args:
            result_id: The ID of the result to load
            
        Returns:
            The ProcessedResult if found, None otherwise
        """
        # Get JSON file path from database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT json_file_path FROM results WHERE id = ?",
                (result_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            json_file_path = row[0]
        
        # Load JSON content
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProcessedResult.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def list_results(self, filter_criteria: Optional[Dict[str, Any]] = None) -> List[ResultSummary]:
        """
        List all results with optional filtering.
        
        Args:
            filter_criteria: Optional dictionary with filter criteria:
                - analysis_type: Filter by analysis type
                - source_type: Filter by source type
                - date_from: Filter results from this date (datetime)
                - date_to: Filter results to this date (datetime)
                - has_visualizations: Filter by visualization presence (bool)
                - has_exportable_data: Filter by exportable data presence (bool)
                - tags: Filter by tags (list of strings)
                - search_text: Search in title and content preview
        
        Returns:
            List of ResultSummary objects
        """
        query = """
            SELECT id, title, analysis_type, source_type, created_at,
                   has_visualizations, has_exportable_data
            FROM results
        """
        params = []
        conditions = []
        
        if filter_criteria:
            if 'analysis_type' in filter_criteria:
                conditions.append("analysis_type = ?")
                params.append(filter_criteria['analysis_type'])
            
            if 'source_type' in filter_criteria:
                conditions.append("source_type = ?")
                params.append(filter_criteria['source_type'])
            
            if 'date_from' in filter_criteria:
                conditions.append("created_at >= ?")
                params.append(filter_criteria['date_from'].isoformat())
            
            if 'date_to' in filter_criteria:
                conditions.append("created_at <= ?")
                params.append(filter_criteria['date_to'].isoformat())
            
            if 'has_visualizations' in filter_criteria:
                conditions.append("has_visualizations = ?")
                params.append(filter_criteria['has_visualizations'])
            
            if 'has_exportable_data' in filter_criteria:
                conditions.append("has_exportable_data = ?")
                params.append(filter_criteria['has_exportable_data'])
            
            if 'search_text' in filter_criteria:
                conditions.append("(title LIKE ? OR content_preview LIKE ?)")
                search_term = f"%{filter_criteria['search_text']}%"
                params.extend([search_term, search_term])
            
            if 'tags' in filter_criteria and filter_criteria['tags']:
                # Search for any of the provided tags
                tag_conditions = []
                for tag in filter_criteria['tags']:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                conditions.append(f"({' OR '.join(tag_conditions)})")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            results = []
            
            for row in cursor.fetchall():
                results.append(ResultSummary(
                    id=row[0],
                    title=row[1],
                    analysis_type=row[2],
                    source_type=row[3] or "unknown",
                    created_at=datetime.fromisoformat(row[4]),
                    has_visualizations=bool(row[5]),
                    has_exportable_data=bool(row[6])
                ))
            
            return results
    
    def delete_result(self, result_id: str) -> bool:
        """
        Delete a result by ID.
        
        Args:
            result_id: The ID of the result to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        # Get JSON file path before deletion
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT json_file_path FROM results WHERE id = ?",
                (result_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return False
            
            json_file_path = row[0]
            
            # Delete from database (inkl. zugehöriger Versionen)
            conn.execute("DELETE FROM result_versions WHERE result_id = ?", (result_id,))
            cursor = conn.execute("DELETE FROM results WHERE id = ?", (result_id,))
            deleted_rows = cursor.rowcount
            conn.commit()
            
            # Delete JSON file
            try:
                os.remove(json_file_path)
            except FileNotFoundError:
                pass  # File already deleted or doesn't exist
            
            return deleted_rows > 0
    
    def export_result(self, result_id: str, format: str = "json") -> Optional[str]:
        """
        Export a result in the specified format.
        
        Args:
            result_id: The ID of the result to export
            format: Export format ("json", "txt", "csv")
            
        Returns:
            Path to exported file if successful, None otherwise
        """
        result = self.load_result(result_id)
        if not result:
            return None
        
        export_dir = self.results_dir / "exports"
        export_dir.mkdir(exist_ok=True)
        
        if format == "json":
            export_path = export_dir / f"{result_id}.json"
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        elif format == "txt":
            export_path = export_dir / f"{result_id}.txt"
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(f"Analyse-Ergebnis: {result.id}\n")
                f.write(f"Erstellt: {result.created_at}\n")
                f.write(f"Typ: {result.metadata.analysis_type}\n")
                if result.source_info:
                    f.write(f"Quelle: {result.source_info.type}\n")
                f.write("\n" + "="*50 + "\n\n")
                f.write(result.content)
        
        elif format == "csv":
            if result.extracted_data.tables:
                export_path = export_dir / f"{result_id}.csv"
                with open(export_path, 'w', encoding='utf-8') as f:
                    # Export first table as CSV
                    f.write(result.extracted_data.tables[0].to_csv_format())
            else:
                return None  # No tabular data to export
        
        else:
            return None  # Unsupported format
        
        return str(export_path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored results.
        
        Returns:
            Dictionary with various statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            # Total count
            cursor = conn.execute("SELECT COUNT(*) FROM results")
            total_count = cursor.fetchone()[0]
            
            # Count by analysis type
            cursor = conn.execute("""
                SELECT analysis_type, COUNT(*) 
                FROM results 
                GROUP BY analysis_type
            """)
            by_analysis_type = dict(cursor.fetchall())
            
            # Count by source type
            cursor = conn.execute("""
                SELECT source_type, COUNT(*) 
                FROM results 
                GROUP BY source_type
            """)
            by_source_type = dict(cursor.fetchall())
            
            # Count with visualizations
            cursor = conn.execute("""
                SELECT COUNT(*) FROM results WHERE has_visualizations = 1
            """)
            with_visualizations = cursor.fetchone()[0]
            
            # Count with exportable data
            cursor = conn.execute("""
                SELECT COUNT(*) FROM results WHERE has_exportable_data = 1
            """)
            with_exportable_data = cursor.fetchone()[0]
            
            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor = conn.execute("""
                SELECT COUNT(*) FROM results WHERE created_at >= ?
            """, (week_ago,))
            recent_count = cursor.fetchone()[0]
            
            return {
                'total_results': total_count,
                'by_analysis_type': by_analysis_type,
                'by_source_type': by_source_type,
                'with_visualizations': with_visualizations,
                'with_exportable_data': with_exportable_data,
                'recent_activity': recent_count
            }
    
    def _generate_title(self, result: ProcessedResult) -> str:
        """
        Generate a title for a result based on its content and metadata.
        
        Args:
            result: The ProcessedResult to generate a title for
            
        Returns:
            Generated title string
        """
        # Try to extract a meaningful title from content
        lines = result.content.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        # If first line looks like a title (short and not ending with punctuation)
        if first_line and len(first_line) < 100 and not first_line.endswith('.'):
            title = first_line
        else:
            # Use analysis type and source info
            title = f"{result.metadata.analysis_type.title()}"
            if result.source_info:
                if result.source_info.file_name:
                    title += f" - {result.source_info.file_name}"
                elif result.source_info.url:
                    title += f" - {result.source_info.url[:50]}..."
        
        # Add timestamp if title is too generic
        if len(title) < 10:
            title += f" - {result.created_at.strftime('%Y-%m-%d %H:%M')}"
        
        return title[:200]  # Limit title length
    
    def update_result(self, result: ProcessedResult) -> bool:
        """
        Update an existing result.
        
        Args:
            result: The updated ProcessedResult
            
        Returns:
            True if updated successfully, False otherwise
        """
        # Update timestamp
        result.update_timestamp()
        
        # Save updated JSON content
        json_file_path = self.results_dir / f"{result.id}.json"
        temporary_json_path = self.results_dir / f".{result.id}.json.tmp"
        backup_json_path = self.results_dir / f".{result.id}.json.bak"
        with open(temporary_json_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # Update database metadata
        replaced_existing = False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE results SET
                        analysis_type = ?,
                        content_preview = ?,
                        has_visualizations = ?,
                        has_exportable_data = ?,
                        processing_time = ?,
                        model_used = ?,
                        tokens_used = ?,
                        confidence_score = ?,
                        tags = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    result.metadata.analysis_type,
                    result.content[:500] + "..." if len(result.content) > 500 else result.content,
                    len(result.visualizations) > 0,
                    result.has_exportable_data(),
                    result.metadata.processing_time,
                    result.metadata.model_used,
                    result.metadata.tokens_used,
                    result.metadata.confidence_score,
                    json.dumps(result.metadata.tags),
                    result.updated_at.isoformat(),
                    result.id
                ))
                if cursor.rowcount == 0:
                    return False
                if json_file_path.exists():
                    os.replace(json_file_path, backup_json_path)
                    replaced_existing = True
                os.replace(temporary_json_path, json_file_path)
                conn.commit()
            if backup_json_path.exists():
                backup_json_path.unlink()
            return True
        except Exception:
            if replaced_existing and backup_json_path.exists():
                if json_file_path.exists():
                    json_file_path.unlink()
                os.replace(backup_json_path, json_file_path)
            raise
        finally:
            if temporary_json_path.exists():
                temporary_json_path.unlink()
            if backup_json_path.exists() and not replaced_existing:
                backup_json_path.unlink()

    # --- Tag-Verwaltung ---

    def add_tag(self, result_id: str, tag: str) -> bool:
        """Fügt ein Tag zu einem Ergebnis hinzu (persistente Speicherung)."""
        tag = tag.strip()
        if not tag:
            return False
        result = self.load_result(result_id)
        if not result:
            return False
        if tag not in result.metadata.tags:
            result.metadata.tags.append(tag)
            return self.update_result(result)
        return True

    def remove_tag(self, result_id: str, tag: str) -> bool:
        """Entfernt ein Tag von einem Ergebnis."""
        result = self.load_result(result_id)
        if not result:
            return False
        if tag in result.metadata.tags:
            result.metadata.tags.remove(tag)
            return self.update_result(result)
        return True

    def get_all_tags(self) -> List[str]:
        """Gibt alle verwendeten Tags (dedupliziert) zurück."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT tags FROM results WHERE tags IS NOT NULL")
            all_tags = set()
            for (tags_json,) in cursor.fetchall():
                try:
                    for tag in json.loads(tags_json):
                        all_tags.add(tag)
                except (json.JSONDecodeError, TypeError):
                    continue
            return sorted(all_tags)

    # --- Favoriten-Verwaltung ---

    def set_favorite(self, result_id: str, is_favorite: bool) -> bool:
        """Markiert ein Ergebnis als Favorit oder entfernt die Markierung."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE results SET is_favorite = ?, updated_at = ? WHERE id = ?",
                (1 if is_favorite else 0, datetime.now().isoformat(), result_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def toggle_favorite(self, result_id: str) -> bool:
        """Schaltet die Favoriten-Markierung um und gibt den neuen Status zurück."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT is_favorite FROM results WHERE id = ?", (result_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return False
            new_state = not bool(row[0])
            self.set_favorite(result_id, new_state)
            return new_state

    def get_favorites(self) -> List[ResultSummary]:
        """Gibt alle als Favorit markierten Ergebnisse zurück."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title, analysis_type, source_type, created_at,
                       has_visualizations, has_exportable_data
                FROM results WHERE is_favorite = 1
                ORDER BY created_at DESC
            """)
            results = []
            for row in cursor.fetchall():
                results.append(ResultSummary(
                    id=row[0],
                    title=row[1],
                    analysis_type=row[2],
                    source_type=row[3] or "unknown",
                    created_at=datetime.fromisoformat(row[4]),
                    has_visualizations=bool(row[5]),
                    has_exportable_data=bool(row[6])
                ))
            return results

    # --- Batch-Export ---

    def batch_export(self, result_ids: List[str], format: str = "json") -> Optional[str]:
        """
        Exportiert mehrere Ergebnisse in ein ZIP-Archiv.

        Args:
            result_ids: Liste der Ergebnis-IDs.
            format: Exportformat ("json", "txt", "csv").

        Returns:
            Pfad zur ZIP-Datei, oder None bei Fehler.
        """
        if not result_ids:
            return None

        export_dir = self.results_dir / "exports"
        export_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = export_dir / f"batch_export_{timestamp}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for rid in result_ids:
                exported = self.export_result(rid, format=format)
                if exported and os.path.exists(exported):
                    zf.write(exported, os.path.basename(exported))

        return str(zip_path)

    # --- Ergebnis-Versionierung ---

    def save_version(self, result_id: str, content: str, note: str = "") -> Optional[str]:
        """Speichert eine Inhaltsversion eines Ergebnisses.

        Returns:
            Versions-ID oder None, wenn das Ergebnis nicht existiert.
        """
        if self.load_result(result_id) is None:
            return None
        version_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(version_no), 0) + 1 FROM result_versions WHERE result_id = ?",
                (result_id,)
            ).fetchone()
            conn.execute(
                "INSERT INTO result_versions (id, result_id, version_no, content, note, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (version_id, result_id, row[0], content, note,
                 datetime.now().isoformat())
            )
            conn.commit()
        return version_id

    def list_versions(self, result_id: str) -> List[Dict[str, Any]]:
        """Listet alle Versionen eines Ergebnisses (neueste zuerst)."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, version_no, note, created_at, LENGTH(content)"
                " FROM result_versions WHERE result_id = ? ORDER BY version_no DESC",
                (result_id,)
            ).fetchall()
        return [
            {
                "id": row[0],
                "version_no": row[1],
                "note": row[2] or "",
                "created_at": row[3],
                "size": row[4],
            }
            for row in rows
        ]

    def get_version_content(self, version_id: str) -> Optional[str]:
        """Gibt den Inhalt einer Version zurück."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT content FROM result_versions WHERE id = ?", (version_id,)
            ).fetchone()
        return row[0] if row else None

    def update_result_content(self, result_id: str, new_content: str,
                              note: str = "Vor Bearbeitung") -> bool:
        """Aktualisiert den Inhalt eines Ergebnisses mit automatischer Vorversion.

        Der bisherige Inhalt wird als Version gesichert, bevor der neue Inhalt
        gespeichert wird – so bleibt jede Bearbeitung rückgängig machbar.
        """
        result = self.load_result(result_id)
        if not result:
            return False
        if result.content == new_content:
            return True
        self.save_version(result_id, result.content, note=note)
        result.content = new_content
        return self.update_result(result)

    def rollback_to_version(self, result_id: str, version_id: str) -> bool:
        """Stellt den Inhalt einer älteren Version wieder her.

        Der aktuelle Inhalt wird vorher als Version gesichert.
        """
        result = self.load_result(result_id)
        if not result:
            return False
        target = self.get_version_content(version_id)
        if target is None:
            return False
        self.save_version(result_id, result.content, note="Vor Wiederherstellung")
        result.content = target
        return self.update_result(result)

    def diff_versions(self, result_id: str, version_id_a: str,
                      version_id_b: str) -> Optional[str]:
        """Erzeugt einen Unified-Diff zwischen zwei Versionen.

        version_id_b darf "current" sein, um mit dem aktuellen Inhalt zu vergleichen.
        """
        import difflib
        content_a = self.get_version_content(version_id_a)
        if version_id_b == "current":
            result = self.load_result(result_id)
            content_b = result.content if result else None
        else:
            content_b = self.get_version_content(version_id_b)
        if content_a is None or content_b is None:
            return None
        return "".join(difflib.unified_diff(
            content_a.splitlines(keepends=True),
            content_b.splitlines(keepends=True),
            fromfile=f"Version {version_id_a[:8]}",
            tofile="aktuell" if version_id_b == "current" else f"Version {version_id_b[:8]}",
        ))