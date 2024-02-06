def find_category_id(name: str, category_list: list[dict]):
    for category in category_list:
        if category['name'] == name:
            return category['id']
    return None
