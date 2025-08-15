def transform_id(data):
    return {**data, "id":str(data.pop("_id"))} if "_id" in data else data
