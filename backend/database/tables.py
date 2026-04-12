"""
SQLAlchemy table definitions (Postgres + PostGIS).

RainUSE Nexus: building-centric schema. Rollups live on ``building_scores``; feature/CV tables
hold inputs and intermediate values (see docs/DATABASE_DECISIONS.md).

Pydantic API models live in ``models/``; this module is the relational schema only.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --- Reference / context -----------------------------------------------------


class StateContextRow(Base):
    """Per-state environmental / utility context (state averages for MVP scoring)."""

    __tablename__ = "state_context"

    state_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    rainfall_inches_annual: Mapped[float] = mapped_column(Float, nullable=False)
    water_price_per_1000_gal_usd: Mapped[float] = mapped_column(Float, nullable=False)


class Company(Base):
    """Corporate owner/operator for ESG and filings linkage."""

    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    ticker: Mapped[str | None] = mapped_column(String, nullable=True)
    cik: Mapped[str | None] = mapped_column(String, nullable=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    hq_state: Mapped[str | None] = mapped_column(String(2), nullable=True)

    buildings: Mapped[list["Building"]] = relationship(back_populates="company")
    sustainability_profile: Mapped["CompanySustainabilityProfile | None"] = relationship(
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["CompanyDocument"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )


class CompanySustainabilityProfile(Base):
    """ESG / climate commitments at company level (SBTi, filings-derived flags)."""

    __tablename__ = "company_sustainability_profiles"

    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    has_esg_report: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_water_target: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_science_based_target: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    climate_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    esg_alignment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Offline SBTi ingest + API provenance (see services/sbti_esg.py, scripts/ingest_sbti_csv.py)
    esg_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    esg_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sbti_ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    esg_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    company: Mapped[Company] = relationship(back_populates="sustainability_profile")


class CompanyDocument(Base):
    """
    SEC / ESG document metadata. Full PDF/HTML bodies are externalized (storage_uri), not stored inline.
    """

    __tablename__ = "company_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[str | None] = mapped_column(String, nullable=True)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    byte_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    company: Mapped[Company] = relationship(back_populates="documents")


# --- Core building -----------------------------------------------------------


class Building(Base):
    """Building/site candidate; everything links back here."""

    __tablename__ = "buildings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    county: Mapped[str | None] = mapped_column(String(256), nullable=True)
    geocode_display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    roof_area_sqft: Mapped[float] = mapped_column(Float, nullable=False)

    company_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    building_type: Mapped[str | None] = mapped_column(String, nullable=True)
    land_use_type: Mapped[str | None] = mapped_column(String, nullable=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    footprint_geom: Mapped[object | None] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326),
        nullable=True,
    )

    # CV snapshot (never overwrites catalog roof_area_sqft / data_source)
    roof_area_sqft_cv: Mapped[float | None] = mapped_column(Float, nullable=True)
    roof_area_confidence_cv: Mapped[float | None] = mapped_column(Float, nullable=True)
    cooling_tower_detected_cv: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    cooling_tower_confidence_cv: Mapped[float | None] = mapped_column(Float, nullable=True)
    cv_inference_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cv_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cv_inference_model: Mapped[str | None] = mapped_column(String(128), nullable=True)

    company: Mapped[Company | None] = relationship(back_populates="buildings")
    scores: Mapped["BuildingScore | None"] = relationship(
        back_populates="building",
        uselist=False,
        cascade="all, delete-orphan",
    )
    imagery_assets: Mapped[list["ImageryAsset"]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
    )
    cv_detections: Mapped[list["CvDetection"]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
    )
    physical_features: Mapped["PhysicalFeature | None"] = relationship(
        back_populates="building",
        uselist=False,
        cascade="all, delete-orphan",
    )
    water_yield_estimate: Mapped["WaterYieldEstimate | None"] = relationship(
        back_populates="building",
        uselist=False,
        cascade="all, delete-orphan",
    )
    utility_profile: Mapped["UtilityProfile | None"] = relationship(
        back_populates="building",
        uselist=False,
        cascade="all, delete-orphan",
    )
    policy_drivers: Mapped[list["PolicyDriver"]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
    )


class ImageryAsset(Base):
    """Satellite / aerial imagery metadata (Sentinel, Landsat, GEE exports, etc.)."""

    __tablename__ = "imagery_assets"

    image_id: Mapped[str] = mapped_column(String, primary_key=True)
    building_id: Mapped[str] = mapped_column(String, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    capture_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    resolution_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    cloud_cover_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    bounding_geom: Mapped[object | None] = mapped_column(Geometry("POLYGON", srid=4326), nullable=True)
    qa_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    building: Mapped[Building] = relationship(back_populates="imagery_assets")
    detections: Mapped[list["CvDetection"]] = relationship(back_populates="imagery_asset")


class CvDetection(Base):
    """Raw CV outputs (roof segment, cooling tower, etc.)."""

    __tablename__ = "cv_detections"

    detection_id: Mapped[str] = mapped_column(String, primary_key=True)
    building_id: Mapped[str] = mapped_column(String, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True)
    image_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("imagery_assets.image_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    detection_type: Mapped[str] = mapped_column(String, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_geom: Mapped[object | None] = mapped_column(Geometry("POLYGON", srid=4326), nullable=True)
    mask_geom: Mapped[object | None] = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)

    building: Mapped[Building] = relationship(back_populates="cv_detections")
    imagery_asset: Mapped[ImageryAsset | None] = relationship(back_populates="detections")


class PhysicalFeature(Base):
    """Interpreted physical features from CV + geometry (inputs to scoring; not the final rollup row)."""

    __tablename__ = "physical_features"

    building_id: Mapped[str] = mapped_column(String, ForeignKey("buildings.id", ondelete="CASCADE"), primary_key=True)
    roof_catchment_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    effective_catchment_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    cooling_tower_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    cooling_tower_count_est: Mapped[float | None] = mapped_column(Float, nullable=True)
    roof_obstruction_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    physical_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    building: Mapped[Building] = relationship(back_populates="physical_features")


class WaterYieldEstimate(Base):
    """Rainwater harvest math (inputs vs rollup on building_scores)."""

    __tablename__ = "water_yield_estimates"

    building_id: Mapped[str] = mapped_column(String, ForeignKey("buildings.id", ondelete="CASCADE"), primary_key=True)
    avg_annual_rainfall_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    runoff_coefficient: Mapped[float | None] = mapped_column(Float, nullable=True)
    system_efficiency_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_harvest_gallons: Mapped[float | None] = mapped_column(Float, nullable=True)
    monthly_harvest_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    water_yield_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    building: Mapped[Building] = relationship(back_populates="water_yield_estimate")


class UtilityProfile(Base):
    """Water / wastewater economics for the site (single current row per building for MVP)."""

    __tablename__ = "utility_profiles"

    building_id: Mapped[str] = mapped_column(String, ForeignKey("buildings.id", ondelete="CASCADE"), primary_key=True)
    water_cost_per_kgal: Mapped[float | None] = mapped_column(Float, nullable=True)
    wastewater_cost_per_kgal: Mapped[float | None] = mapped_column(Float, nullable=True)
    stormwater_fee_monthly: Mapped[float | None] = mapped_column(Float, nullable=True)
    utility_cost_pressure_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    building: Mapped[Building] = relationship(back_populates="utility_profile")


class PolicyDriver(Base):
    """Incentives / fees / regulatory signals (many rows per building)."""

    __tablename__ = "policy_drivers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    building_id: Mapped[str] = mapped_column(String, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True)
    jurisdiction_name: Mapped[str | None] = mapped_column(String, nullable=True)
    policy_type: Mapped[str | None] = mapped_column(String, nullable=True)
    policy_name: Mapped[str | None] = mapped_column(String, nullable=True)
    estimated_value_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    driver_strength_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    building: Mapped[Building] = relationship(back_populates="policy_drivers")


class BuildingScore(Base):
    """
    Canonical rollup scores for a building (single current row per building).

    Pillar fields are nullable until the scoring pipeline populates them.
    detection_confidence_score is aggregated from cv_detections in code, not copied raw from CSV.
    """

    __tablename__ = "building_scores"

    building_id: Mapped[str] = mapped_column(String, ForeignKey("buildings.id", ondelete="CASCADE"), primary_key=True)

    physical_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_yield_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    utility_cost_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    regulatory_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    corporate_esg_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    climate_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Drought / water stress and similar rolled into this pillar as agreed.",
    )
    detection_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    final_viability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    opportunity_tier: Mapped[str | None] = mapped_column(String, nullable=True)

    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    building: Mapped[Building] = relationship(back_populates="scores")

# API keys: see ``database.api_keys_dataset`` (separate module to reduce merge churn).
