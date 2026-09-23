# src/workers/ufdr_parser_worker.py
"""
Worker Especializado de Parsing Forense para Extrações Cellebrite UFDR.
Opera em streaming iterativo via zipfile para garantir baixo consumo de memória RAM (< 512 MB).
Suporta extração do catálogo de arquivos (taggedFiles) e eventos decodificados (decodedData).
"""
import zipfile
import xml.etree.ElementTree as ET
import re
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional, Generator
import os

class UFDRStreamingParser:
    def __init__(self, ufdr_path: str):
        if not os.path.exists(ufdr_path):
            raise FileNotFoundError(f"Arquivo UFDR não encontrado: {ufdr_path}")
        self.ufdr_path = ufdr_path

    def extract_device_metadata(self) -> Dict[str, Any]:
        """
        Lê apenas os primeiros bytes de report.xml para extrair metadados essenciais de hardware e do exame.
        """
        metadata = {
            "model_number": None,
            "vendor": None,
            "imei": None,
            "android_id": None,
            "pa_version": None,
            "examiner": None,
            "department": None,
            "extraction_time": None,
            "timezone": None,
        }

        with zipfile.ZipFile(self.ufdr_path, "r") as z:
            with z.open("report.xml") as f:
                header_chunk = f.read(500 * 1024).decode("utf-8", errors="ignore")

                m_imei = re.search(r'name="IMEI"[^>]*><!\[CDATA\[([^\]]+)\]\]>', header_chunk)
                if m_imei: metadata["imei"] = m_imei.group(1)

                m_model = re.search(r'name="DeviceInfoModelNumber"[^>]*><!\[CDATA\[([^\]]+)\]\]>', header_chunk)
                if m_model: metadata["model_number"] = m_model.group(1)

                m_vendor = re.search(r'name="DeviceInfoDetectedPhoneVendor"[^>]*><!\[CDATA\[([^\]]+)\]\]>', header_chunk)
                if m_vendor: metadata["vendor"] = m_vendor.group(1)

                m_pa = re.search(r'name="UFED_PA_Version"[^>]*><!\[CDATA\[([^\]]+)\]\]>', header_chunk)
                if m_pa: metadata["pa_version"] = m_pa.group(1)

                m_android_id = re.search(r'name="DeviceInfoAndroidID"[^>]*><!\[CDATA\[([^\]]+)\]\]>', header_chunk)
                if m_android_id: metadata["android_id"] = m_android_id.group(1)

                m_exam = re.search(r'fieldName="ExaminerName"[^>]*>([^<]+)<', header_chunk)
                if m_exam: metadata["examiner"] = m_exam.group(1)

                m_tz = re.search(r'name="Time Zone"[^>]*><!\[CDATA\[([^\]]+)\]\]>', header_chunk)
                if m_tz: metadata["timezone"] = m_tz.group(1)

        return metadata

    def iterate_tagged_files(
        self,
        tenant_id: str = "tenant_default",
        case_id: str = "case_default",
        evidence_id: str = "ev_default",
        ingestion_id: str = "ingest_default"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Gera iterativamente os metadados de cada arquivo registrado na partição (taggedFiles).
        Mapeia diretamente para a tabela canônica silver.forensic_artifacts.
        """
        with zipfile.ZipFile(self.ufdr_path, "r") as z:
            with z.open("report.xml") as xml_file:
                for event, elem in ET.iterparse(xml_file, events=("end",)):
                    tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                    if tag_name == "file":
                        file_id = elem.attrib.get("id") or str(uuid.uuid4())
                        file_path = elem.attrib.get("path") or "UNKNOWN_PATH"
                        size_str = elem.attrib.get("size", "0")
                        deleted_status = elem.attrib.get("deleted", "Intact")

                        created_at = None
                        modified_at = None
                        accessed_at = None
                        sha256 = None
                        md5 = None
                        inode = None

                        for child in elem:
                            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                            if child_tag == "accessInfo":
                                for ts in child:
                                    ts_name = ts.attrib.get("name")
                                    ts_val = ts.text or ts.attrib.get("formattedTimestamp")
                                    if ts_name == "CreationTime": created_at = ts_val
                                    elif ts_name == "ModifyTime": modified_at = ts_val
                                    elif ts_name == "AccessTime": accessed_at = ts_val
                            elif child_tag == "metadata":
                                for item in child:
                                    item_name = item.attrib.get("name")
                                    item_text = item.text
                                    if item_name == "SHA256": sha256 = item_text
                                    elif item_name == "MD5": md5 = item_text
                                    elif item_name == "Inode Number": inode = item_text

                        record = {
                            "artifact_id": file_id,
                            "tenant_id": tenant_id,
                            "case_id": case_id,
                            "evidence_id": evidence_id,
                            "file_path": file_path,
                            "file_name": os.path.basename(file_path) if file_path else "",
                            "size_bytes": int(size_str) if size_str.isdigit() else 0,
                            "deleted_status": deleted_status,
                            "created_at": created_at,
                            "modified_at": modified_at,
                            "accessed_at": accessed_at,
                            "sha256": sha256,
                            "md5": md5,
                            "inode": inode,
                            "ingestion_id": ingestion_id,
                        }

                        yield record
                        elem.clear()

    def iterate_decoded_events(
        self,
        tenant_id: str = "tenant_default",
        case_id: str = "case_default",
        evidence_id: str = "ev_default",
        ingestion_id: str = "ingest_default"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Gera iterativamente os eventos de comunicações e dispositivo extraídos (decodedData).
        Mapeia diretamente para a tabela canônica silver.forensic_events.
        """
        with zipfile.ZipFile(self.ufdr_path, "r") as z:
            with z.open("report.xml") as xml_file:
                for event, elem in ET.iterparse(xml_file, events=("end",)):
                    tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                    if tag_name == "model":
                        m_type = elem.attrib.get("type")
                        m_id = elem.attrib.get("id") or str(uuid.uuid4())

                        # Extrai todos os campos internos do modelo
                        fields = {}
                        for child in elem:
                            fname = child.attrib.get("name")
                            val = None
                            val_elem = child.find("{http://pa.cellebrite.com/report/2.0}value")
                            if val_elem is not None:
                                val = val_elem.text
                            elif child.text and child.text.strip():
                                val = child.text.strip()
                            if fname:
                                fields[fname] = val

                        event_category = "OTHER"
                        event_type = m_type.upper()
                        event_timestamp = None
                        actor_from = None
                        actor_to = None
                        content_summary = None
                        source_app = fields.get("Source") or fields.get("SourceApplication")

                        if m_type == "InstantMessage":
                            event_category = "MESSAGE"
                            event_type = "INSTANT_MESSAGE"
                            event_timestamp = fields.get("TimeStamp")
                            actor_from = fields.get("From")
                            actor_to = fields.get("To")
                            content_summary = fields.get("Body")
                        elif m_type == "Chat":
                            event_category = "MESSAGE"
                            event_type = "CHAT_SESSION"
                            event_timestamp = fields.get("StartTime") or fields.get("LastActivity")
                            content_summary = fields.get("Name")
                        elif m_type == "Call":
                            event_category = "CALL"
                            event_type = "VOICE_CALL"
                            event_timestamp = fields.get("TimeStamp")
                            actor_from = fields.get("From")
                            actor_to = fields.get("To")
                            content_summary = f"Duration: {fields.get('Duration', 'N/A')}s"
                        elif m_type == "DeviceEvent":
                            event_category = "DEVICE"
                            event_type = fields.get("EventType", "DEVICE_EVENT").upper()
                            event_timestamp = fields.get("StartTime") or fields.get("TimeStamp")
                            content_summary = f"{fields.get('EventType')}: {fields.get('Value')}"
                        elif m_type == "VisitedPage":
                            event_category = "WEB"
                            event_type = "PAGE_VISIT"
                            event_timestamp = fields.get("LastVisited") or fields.get("TimeStamp")
                            content_summary = fields.get("Title") or fields.get("Url")
                        elif m_type == "Location":
                            event_category = "LOCATION"
                            event_type = "GPS_COORDINATE"
                            event_timestamp = fields.get("TimeStamp")
                            content_summary = f"{fields.get('Name')} ({fields.get('Category')})"
                        elif m_type == "WirelessNetwork":
                            event_category = "NETWORK"
                            event_type = "WIFI_CONNECTION"
                            event_timestamp = fields.get("TimeStamp") or fields.get("LastConnection")
                            content_summary = f"SSID: {fields.get('SSId')} | BSSID: {fields.get('BSSId')}"
                        elif m_type == "InstalledApplication":
                            event_category = "APP"
                            event_type = "APP_INSTALLED"
                            event_timestamp = fields.get("PurchaseDate") or fields.get("LastLaunched")
                            content_summary = f"{fields.get('Identifier')} (v{fields.get('Version')})"
                        elif m_type == "Password":
                            event_category = "PASSWORD"
                            event_type = "CREDENTIAL_STORED"
                            event_timestamp = fields.get("TimeStamp")
                            content_summary = f"Service: {fields.get('ServiceIdentifier') or fields.get('Name')}"

                        # Filtra apenas registros com timestamp válido
                        if event_timestamp:
                            record = {
                                "event_id": m_id,
                                "tenant_id": tenant_id,
                                "case_id": case_id,
                                "evidence_id": evidence_id,
                                "event_category": event_category,
                                "event_type": event_type,
                                "event_timestamp": event_timestamp,
                                "actor_from": actor_from,
                                "actor_to": actor_to,
                                "content_summary": content_summary,
                                "source_application": source_app,
                                "raw_payload_json": json.dumps(fields, ensure_ascii=False),
                                "ingestion_id": ingestion_id,
                            }
                            yield record

                        elem.clear()
