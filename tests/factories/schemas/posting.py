import uuid

from factory import Factory, Faker, LazyAttribute, List, SubFactory
from schemas.posting import CreatePostingRequest, OrderedGood


class OrderedGoodFactory(Factory):
    class Meta:
        model = OrderedGood
        # Альтернативный вариант без class Params
        # exclude = (
        #     'valid_ids_count',
        #     'defect_ids_count',
        # )

    # valid_ids_count = Faker('pyint', min_value=1, max_value=5)
    # defect_ids_count = Faker('pyint', min_value=1, max_value=5)

    # Добавление параметров для управления количеством сгенерированных сущностей
    # https://factoryboy.readthedocs.io/en/stable/introduction.html#altering-a-factory-s-behavior-parameters-and-traits
    class Params:
        valid_ids_count = Faker('pyint', min_value=1, max_value=5)
        defect_ids_count = Faker('pyint', min_value=1, max_value=5)

    sku = Faker('uuid4')
    from_valid_ids = LazyAttribute(lambda obj: [uuid.uuid4() for _ in range(obj.valid_ids_count)])
    from_defect_ids = LazyAttribute(lambda obj: [uuid.uuid4() for _ in range(obj.defect_ids_count)])


class CreatePostingRequestFactory(Factory):
    class Meta:
        model = CreatePostingRequest

    ordered_goods = List([SubFactory(OrderedGoodFactory)])
