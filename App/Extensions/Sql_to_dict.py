from sqlalchemy.orm import object_mapper
def model_to_dict(model,seen = None):
        if seen is None:
            seen = set()

        if id(model) in seen:
            return None  # Avoid infinite loops

        seen.add(id(model))
        result = {}
        for column in model.__table__.columns:
            result[column.name] = getattr(model, column.name)

        # Handle relationships
        for rel in object_mapper(model).relationships:
            related_models = getattr(model, rel.key)
            if related_models is not None:
                if rel.uselist:
                    Result = [model_to_dict(child,seen) for child in related_models]
                else:
                    Result = model_to_dict(related_models,seen)
                if(Result):
                    result[rel.key] = Result
        return result
    
def list_to_dict(model_list):
    return [model_to_dict(model) for model in model_list]

def map_model_to_dto(model_instance, dto_class):
    result_dict = model_to_dict(model_instance)
    dto_instance = dto_class()

    for key, value in result_dict.items():
        setattr(dto_instance, key, value)

    return dto_instance

def list_to_dto(model_list,dto_class):
    return [map_model_to_dto(model,dto_class) for model in model_list]
