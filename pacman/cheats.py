"""Transient review tools, always reset when a new run begins."""

from dataclasses import dataclass


@dataclass
class Cheats:
    """Store toggles independently from the normal game rules."""

    enabled: bool = False
    invincible: bool = False
    frozen: bool = False

    def toggle(self) -> None:
        """Toggle review mode and clear persistent effects when disabled."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.invincible = False
            self.frozen = False
