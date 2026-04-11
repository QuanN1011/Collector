"""
SQLAlchemy table definitions (Postgres + PostGIS).

Pydantic API models live in `models/`; this module is the relational schema only.
"""

from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class StateContextRow(Base):
    """Per-state environmental / utility context used in scoring (state averages)."""

    __tablename__ = "state_context"

    state_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    rainfall_inches_annual: Mapped[float] = mapped_column(Float, nullable=False)
    water_price_per_1000_gal_usd: Mapped[float] = mapped_column(Float, nullable=False)


class Building(Base):
    """Building/site candidate; everything links back here."""

    __tablename__ = "buildings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    roof_area_sqft: Mapped[float] = mapped_column(Float, nullable=False)

    # Hackathon choice: lat/lon columns for map pins and simple APIs (less ORM friction than raw WKB).
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Optional footprint for accuracy (roof/parcel); SRID 4326. Bbox queries can use this + GiST later.
    footprint_geom: Mapped[object | None] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326),
        nullable=True,
    )

    scores: Mapped["BuildingScore | None"] = relationship(
        back_populates="building",
        uselist=False,
        cascade="all, delete-orphan",
    )


class BuildingScore(Base):
    """
    Canonical rollup scores for a building (single current row per building).

    Raw inputs live in feature/CV tables later; *component* scores on those tables should not
    duplicate names here (hackathon rule: inputs vs rollups).

    Tower / CV confidences are aggregated into detection_confidence_score in the scoring pipeline,
    not copied from the dataset verbatim.
    """

    __tablename__ = "building_scores"

    building_id: Mapped[str] = mapped_column(String, ForeignKey("buildings.id", ondelete="CASCADE"), primary_key=True)
    final_viability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    climate_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Includes drought / water stress as agreed: treat as climate_risk_score.",
    )
    corporate_esg_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    detection_confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Rollup from cv_detections / pipeline; computed later, not a raw dataset field.",
    )
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    building: Mapped[Building] = relationship(back_populates="scores")
