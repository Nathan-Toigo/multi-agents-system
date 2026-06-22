from .stock import (
    list_stocks,
    get_stock_alerts,
    add_to_stock,
    remove_from_stock,
    create_stock_item,
)
from .production import (
    list_productions,
    create_production_order,
    start_production,
    complete_production,
)
from .order import (
    list_orders,
    create_order,
    update_order_status,
)
from .machine import (
    list_machines,
    get_machine,
    set_machine_status,
)
from .rag import search_documentation

ALL_TOOLS = [
    # Stock
    list_stocks,
    get_stock_alerts,
    add_to_stock,
    remove_from_stock,
    create_stock_item,
    # Production
    list_productions,
    create_production_order,
    start_production,
    complete_production,
    # Commandes
    list_orders,
    create_order,
    update_order_status,
    # Machines
    list_machines,
    get_machine,
    set_machine_status,
    # Documentation RAG
    search_documentation,
]
