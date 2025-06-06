import json


def create_gtfs_ontology(class_name, source_file, fields):
    ontology = {
        "nodes": [{"id": class_name, "label": class_name, "type": "class", "source_file": source_file}],
        "edges": []
    }

    for field in fields:
        node = {
            "id": field["name"],
            "label": field["name"],
            "type": "objectProperty" if field.get("foreign_key") else "datatypeProperty",
            "value_type": field["value_type"],
            "required": field["required"],
            "description": field["description"],
            "gtfs_type": field["gtfs_type"]
        }

        if field.get("foreign_key"):
            node["target_class"] = field["foreign_key"]
        if field.get("enum_values"):
            node["enum_values"] = field["enum_values"]

        ontology["nodes"].append(node)
        ontology["edges"].append({
            "from": class_name,
            "to": field["name"],
            "label": "hasProperty"
        })

    return ontology

# Exemple d’utilisation pour routes.txt
routes_fields = [
    {"name": "route_id", "value_type": "string", "required": True, "description": "Identifiant de la ligne", "gtfs_type": "ID"},
    {"name": "agency_id", "value_type": "string", "required": "conditional", "description": "Agence opératrice", "gtfs_type": "Foreign ID", "foreign_key": "Agency"},
    {"name": "route_short_name", "value_type": "string", "required": "conditional", "description": "Nom court", "gtfs_type": "Text"},
    {"name": "route_long_name", "value_type": "string", "required": "conditional", "description": "Nom long", "gtfs_type": "Text"},
    {"name": "route_desc", "value_type": "string", "required": False, "description": "Description", "gtfs_type": "Text"},
    {"name": "route_type", "value_type": "enum", "required": True, "description": "Type de transport", "gtfs_type": "Enum", "enum_values": [0, 1, 2, 3, 4, 5, 6, 7]},
    {"name": "route_url", "value_type": "url", "required": False, "description": "Lien web", "gtfs_type": "URL"},
    {"name": "route_color", "value_type": "color", "required": False, "description": "Couleur ligne", "gtfs_type": "Color"},
    {"name": "route_text_color", "value_type": "color", "required": False, "description": "Couleur texte", "gtfs_type": "Color"},
    {"name": "route_sort_order", "value_type": "integer", "required": False, "description": "Tri d’affichage", "gtfs_type": "Integer"},
    {"name": "continuous_pickup", "value_type": "enum", "required": False, "description": "Embarquement continu", "gtfs_type": "Enum", "enum_values": [0, 1, 2, 3]},
    {"name": "continuous_drop_off", "value_type": "enum", "required": False, "description": "Débarquement continu", "gtfs_type": "Enum", "enum_values": [0, 1, 2, 3]}
]

ontology = create_gtfs_ontology("Route", "routes.txt", routes_fields)

with open("routes_ontology.json", "w", encoding="utf-8") as f:
    json.dump(ontology, f, indent=2, ensure_ascii=False)
