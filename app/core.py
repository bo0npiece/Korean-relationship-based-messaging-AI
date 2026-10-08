"""기능들이 공통으로 쓰는 부품 묶음. app.state.core 에 하나만 만들어 둠."""
from dataclasses import dataclass

from .config import Settings
from .customize import Customize
from .hcx import HCXClient
from .stores.contact_store import ContactStore
from .stores.rehearsal_store import RehearsalStore
from .services.knowledge import KnowledgeBase


@dataclass
class Core:
    settings: Settings
    hcx: HCXClient
    customize: Customize
    knowledge: KnowledgeBase
    contacts: ContactStore
    rehearsals: RehearsalStore

    @classmethod
    def build(cls, settings: Settings) -> "Core":
        hcx = HCXClient(settings)
        return cls(
            settings=settings,
            hcx=hcx,
            customize=Customize(settings.customize_dir),
            knowledge=KnowledgeBase(hcx, settings.customize_dir / "knowledge", settings.data_dir),
            contacts=ContactStore(settings.db_path),
            rehearsals=RehearsalStore(settings.db_path),
        )
