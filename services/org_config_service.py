"""
services/org_config_service.py
------------------------------
Organization & Workspace Configuration Service for Avyara.

Supports tailoring Avyara for diverse industrial enterprises without hardcoding
refinery-only terminology across every module. Provides configurable:
- Organization Name
- Industry Sector
- Active Workspaces / Project Units
- Domain-Specific Terminology (Asset ID, Inspection Audit, Drawing / Blueprint, Compliance Standards)
- Enabled Workbench Modules

Offers refinery-oriented defaults for the SIH demonstration (MRPL CDU-1),
with instant 1-click industry presets for Automotive, Aerospace, Pharma, and Power Utilities.
"""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CONFIG_DIR = Path("config")
CONFIG_FILE = CONFIG_DIR / "organization.json"

DEFAULT_ORGANIZATION: Dict[str, Any] = {
    "org_id": "org_mrpl",
    "org_name": "Mangalore Refinery & Petrochemicals (MRPL)",
    "industry": "Refinery & Petrochemicals",
    "facility_location": "Mangalore, Karnataka, India",
    "active_workspace_id": "ws_cdu1",
    "workspaces": [
        {
            "id": "ws_cdu1",
            "name": "Crude Distillation Unit 1 (CDU-1)",
            "description": "Atmospheric & Vacuum crude fractionation train",
            "unit_code": "U-100",
        },
        {
            "id": "ws_utilities",
            "name": "Plant Utilities & Power Block",
            "description": "High-pressure boiler feed pump networks & cooling towers",
            "unit_code": "U-400",
        },
        {
            "id": "ws_tankfarm",
            "name": "Tank Farm & Offsite Piping",
            "description": "Finished product hydrocarbon storage manifolds & custody transfer",
            "unit_code": "U-700",
        },
    ],
    "terminology": {
        "asset_label": "Equipment Tag",
        "inspection_label": "Statutory Integrity Audit",
        "drawing_label": "P&ID Schematic",
        "standard_label": "OISD / API / ISO Standard",
        "defect_label": "Observed Non-Conformance",
        "telemetry_label": "Process Telemetry Reading",
    },
    "enabled_modules": [
        "dashboard",
        "document",
        "defect",
        "drawing",
        "reports",
        "sop",
        "sandbox",
        "spreadsheet",
        "files",
        "audit",
        "settings",
    ],
}

INDUSTRY_PRESETS: Dict[str, Dict[str, Any]] = {
    "refinery": {
        "id": "refinery",
        "name": "Refinery & Petrochemicals (MRPL / SIH Default)",
        "org_name": "Mangalore Refinery & Petrochemicals (MRPL)",
        "industry": "Refinery & Petrochemicals",
        "facility_location": "Mangalore, Karnataka, India",
        "active_workspace_id": "ws_cdu1",
        "workspaces": [
            {
                "id": "ws_cdu1",
                "name": "Crude Distillation Unit 1 (CDU-1)",
                "description": "Atmospheric & Vacuum crude fractionation train",
                "unit_code": "U-100",
            },
            {
                "id": "ws_utilities",
                "name": "Plant Utilities & Power Block",
                "description": "High-pressure boiler feed pump networks & cooling towers",
                "unit_code": "U-400",
            },
            {
                "id": "ws_tankfarm",
                "name": "Tank Farm & Offsite Piping",
                "description": "Finished product hydrocarbon storage manifolds & custody transfer",
                "unit_code": "U-700",
            },
        ],
        "terminology": {
            "asset_label": "Equipment Tag",
            "inspection_label": "Statutory Integrity Audit",
            "drawing_label": "P&ID Schematic",
            "standard_label": "OISD / API Standard",
            "defect_label": "Observed Non-Conformance",
            "telemetry_label": "Process Telemetry Reading",
        },
    },
    "automotive": {
        "id": "automotive",
        "name": "Automotive & Heavy Manufacturing",
        "org_name": "Precision Dynamics Motor Works",
        "industry": "Automotive & Robotics Assembly",
        "facility_location": "Chennai Automotive Corridor, India",
        "active_workspace_id": "ws_body_shop",
        "workspaces": [
            {
                "id": "ws_body_shop",
                "name": "Automated Body-in-White (BIW) Cell",
                "description": "Robotic resistance spot welding and chassis alignment line",
                "unit_code": "CELL-04",
            },
            {
                "id": "ws_paint",
                "name": "Cathodic Electrodeposition & Paint Shop",
                "description": "Substrate pre-treatment and electrostatic primer spray booths",
                "unit_code": "PAINT-02",
            },
            {
                "id": "ws_powertrain",
                "name": "Electric Drive Unit & Inverter Assembly",
                "description": "Stator winding, rotor balancing and dyno testing line",
                "unit_code": "EDU-01",
            },
        ],
        "terminology": {
            "asset_label": "Station / Tool ID",
            "inspection_label": "Quality Gate Verification",
            "drawing_label": "Wiring & Pneumatic Blueprint",
            "standard_label": "IATF 16949 / ISO 9001 Standard",
            "defect_label": "Assembly Discrepancy",
            "telemetry_label": "Sensor In-Line Gauge",
        },
    },
    "aerospace": {
        "id": "aerospace",
        "name": "Aerospace & Propulsion Systems",
        "org_name": "Skybound Aero Propulsion Dynamics",
        "industry": "Aerospace & Defense Structures",
        "facility_location": "Bengaluru Aerospace Park, India",
        "active_workspace_id": "ws_turbines",
        "workspaces": [
            {
                "id": "ws_turbines",
                "name": "Gas Turbine Hot-Section Assembly",
                "description": "Single-crystal nickel alloy turbine blade and stator shrouds",
                "unit_code": "BLD-7A",
            },
            {
                "id": "ws_avionics",
                "name": "Fly-by-Wire Actuator Integration",
                "description": "Hydraulic manifold and primary flight control surface actuators",
                "unit_code": "ACT-3B",
            },
            {
                "id": "ws_composites",
                "name": "Carbon Composite Autoclave Bay",
                "description": "Wing spar pre-preg layups and high-pressure cure cycles",
                "unit_code": "BAY-12",
            },
        ],
        "terminology": {
            "asset_label": "Part / Serial Number",
            "inspection_label": "Airworthiness Conformity Inspection",
            "drawing_label": "Engineering Assembly Drawing",
            "standard_label": "AS9100 / FAA / DGCA Standard",
            "defect_label": "Structural Non-Conformance",
            "telemetry_label": "Calibration Metric",
        },
    },
    "pharmaceutical": {
        "id": "pharmaceutical",
        "name": "Pharmaceutical & Sterile Biologics",
        "org_name": "AuraBio Sterile Therapeutics",
        "industry": "Pharmaceutical & Life Sciences",
        "facility_location": "Hyderabad Genome Valley, India",
        "active_workspace_id": "ws_fermentation",
        "workspaces": [
            {
                "id": "ws_fermentation",
                "name": "Bioreactor Fermentation Suite A",
                "description": "5000L Stainless Steel Jacketed Cell Culture Bioreactors",
                "unit_code": "BIO-01",
            },
            {
                "id": "ws_fill_finish",
                "name": "Aseptic Isolator Fill & Finish Line",
                "description": "Grade A laminar flow robotic vial filling and freeze drying",
                "unit_code": "ISO-03",
            },
            {
                "id": "ws_wfi",
                "name": "Water for Injection (WFI) Loop",
                "description": "Multi-effect distillation column and continuous ozone loop",
                "unit_code": "WFI-02",
            },
        ],
        "terminology": {
            "asset_label": "Validation Tag ID",
            "inspection_label": "GMP Cleanroom Batch Audit",
            "drawing_label": "Process Flow Diagram (PFD)",
            "standard_label": "US FDA / cGMP / ISO 14644 Standard",
            "defect_label": "Batch Deviation / OOS",
            "telemetry_label": "Validated SCADA Parameter",
        },
    },
    "pharma": {
        "id": "pharma",
        "name": "Pharmaceutical & Sterile Biologics",
        "org_name": "AuraBio Sterile Therapeutics",
        "industry": "Pharmaceutical & Life Sciences",
        "facility_location": "Hyderabad Genome Valley, India",
        "active_workspace_id": "ws_fermentation",
        "workspaces": [
            {
                "id": "ws_fermentation",
                "name": "Bioreactor Fermentation Suite A",
                "description": "5000L Stainless Steel Jacketed Cell Culture Bioreactors",
                "unit_code": "BIO-01",
            },
            {
                "id": "ws_fill_finish",
                "name": "Aseptic Isolator Fill & Finish Line",
                "description": "Grade A laminar flow robotic vial filling and freeze drying",
                "unit_code": "ISO-03",
            },
            {
                "id": "ws_wfi",
                "name": "Water for Injection (WFI) Loop",
                "description": "Multi-effect distillation column and continuous ozone loop",
                "unit_code": "WFI-02",
            },
        ],
        "terminology": {
            "asset_label": "Validation Tag ID",
            "inspection_label": "GMP Cleanroom Batch Audit",
            "drawing_label": "Process Flow Diagram (PFD)",
            "standard_label": "US FDA / cGMP / ISO 14644 Standard",
            "defect_label": "Batch Deviation / OOS",
            "telemetry_label": "Validated SCADA Parameter",
        },
    },
}


class OrgConfigService:
    """Thread-safe persistent configuration service for multi-enterprise deployment."""

    _instance: Optional["OrgConfigService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "OrgConfigService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_service()
            return cls._instance

    def _init_service(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._config: Dict[str, Any] = DEFAULT_ORGANIZATION.copy()
        self._load()

    def _load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Merge with defaults
                        self._config.update(data)
                        logger.info("OrgConfigService: Loaded configuration for '%s'", self._config.get("org_name"))
            except Exception as exc:
                logger.warning("OrgConfigService: Error loading config file: %s. Using defaults.", exc)

    def _save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
            logger.info("OrgConfigService: Saved configuration for '%s'", self._config.get("org_name"))
        except Exception as exc:
            logger.warning("OrgConfigService: Error saving config file: %s", exc)

    def get_config(self) -> Dict[str, Any]:
        """Returns active organization and workspace configuration."""
        with self._lock:
            return dict(self._config)

    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates organization parameters and persists to disk."""
        with self._lock:
            # Disallow removing required keys
            for key in ["org_name", "industry", "workspaces", "terminology", "enabled_modules", "facility_location"]:
                if key in updates:
                    self._config[key] = updates[key]

            if "active_workspace_id" in updates:
                ws_ids = [w["id"] for w in self._config.get("workspaces", [])]
                if updates["active_workspace_id"] in ws_ids:
                    self._config["active_workspace_id"] = updates["active_workspace_id"]

            self._save()
            return dict(self._config)

    def get_presets(self) -> List[Dict[str, Any]]:
        """Returns selectable industry presets."""
        return list(INDUSTRY_PRESETS.values())

    def apply_preset(self, preset_id: str) -> Dict[str, Any]:
        """Applies a preset template while preserving enabled modules."""
        with self._lock:
            preset = INDUSTRY_PRESETS.get(preset_id)
            if not preset:
                raise ValueError(f"Unknown preset ID: {preset_id}")

            self._config["org_id"] = f"org_{preset_id}"
            self._config["org_name"] = preset["org_name"]
            self._config["industry"] = preset["industry"]
            self._config["facility_location"] = preset["facility_location"]
            self._config["active_workspace_id"] = preset["active_workspace_id"]
            self._config["workspaces"] = preset["workspaces"]
            self._config["terminology"] = preset["terminology"]

            self._save()
            return dict(self._config)

    def switch_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """Switches the active workspace."""
        with self._lock:
            ws_ids = [w["id"] for w in self._config.get("workspaces", [])]
            if workspace_id not in ws_ids:
                raise ValueError(f"Workspace '{workspace_id}' not found in active organization.")
            self._config["active_workspace_id"] = workspace_id
            self._save()
            return dict(self._config)


org_config_service = OrgConfigService()
