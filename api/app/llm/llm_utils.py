import os, yaml

def load_semantic_map():
    file_path = os.path.join(os.path.dirname(__file__), "semantic_map.yaml")
    with open(file_path) as f:
        m = yaml.safe_load(f)

    mappings_str = []
    for term, info in m.items():
        cols = ", ".join(info["columns"])
        mappings_str.append(f"- '{term}'. {info['description']} → [{cols}]")

    return "\n".join(mappings_str)

