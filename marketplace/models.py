import datetime
import enum
import uuid
from decimal import Decimal
from typing import Annotated

from app import database
from schemas.discount import DiscountSchema, DiscountSchemaStatus
from service_models import DiscountDTO
from sqlalchemy import DECIMAL, UUID, CheckConstraint, DateTime, ForeignKey, sql, text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class DiscountStatus(enum.StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"


discount_status_to_discount_schema_status_map = {
    # TODO: Подумать и убрать отсюда схемы API
    DiscountStatus.ACTIVE: DiscountSchemaStatus.ACTIVE,
    DiscountStatus.FINISHED: DiscountSchemaStatus.FINISHED,
}

uuid_pk = Annotated[uuid.UUID, mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    # TODO: Подумать стоит ли делать server_default и как
    default=uuid.uuid4,
)]
created_at = Annotated[datetime.datetime, mapped_column(
    DateTime(timezone=True),
    server_default=text("TIMEZONE('utc', now())"),
)]
updated_at = Annotated[datetime.datetime, mapped_column(
    DateTime(timezone=True),
    server_default=text("TIMEZONE('utc', now())"),
    onupdate=datetime.datetime.now(datetime.UTC),
)]
# https://stackoverflow.com/questions/27869239/sqlalchemy-decimal-precision
# https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.DECIMAL
price = Annotated[Decimal, mapped_column(type_=DECIMAL(scale=2))]


class Discount(database.Base):
    __tablename__ = "discounts"

    id: Mapped[uuid_pk]
    status: Mapped[DiscountStatus]
    created_at: Mapped[created_at]
    # TODO: Подумать нужно ли добавлять данное поле и логику
    # finished_at: AwareDatetime
    # TODO: Добавить ограничение - не более 100% или 99% и не меньше 0 или 1
    percentage: Mapped[int]

    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#declarative-vs-imperative-forms
    skus: Mapped[list["Sku"]] = relationship("Sku", back_populates='discount')

    item_discounts: Mapped[list["ItemDiscount"]] = relationship("ItemDiscount", back_populates='discount')

    def to_read_model(self) -> DiscountSchema:
        return DiscountSchema(
            id=self.id,
            status=discount_status_to_discount_schema_status_map.get(self.status),
            created_at=self.created_at,
            percentage=self.percentage,
            sku_ids=[sku.id for sku in self.skus],
        )

    def as_dto(self) -> DiscountDTO:
        return DiscountDTO.model_validate(self)


class Sku(database.Base):
    """Уникальная товарная группа"""
    __tablename__ = "skus"
    __table_args__ = (
        # https://docs.sqlalchemy.org/en/20/core/constraints.html#sqlalchemy.schema.CheckConstraint
        CheckConstraint("actual_price >= 0", name="actual_price_positive"),
        CheckConstraint("base_price >= 0", name="base_price_positive"),
    )

    id: Mapped[uuid_pk]
    created_at: Mapped[created_at]
    # TODO: Возможно стоит сделать | None? Подумать над данным моментом
    actual_price: Mapped[price]
    base_price: Mapped[price]
    count: Mapped[int] = mapped_column(default=0)
    is_hidden: Mapped[bool] = mapped_column(server_default=sql.false())

    discount_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("discounts.id"))
    # TODO: Оказывается тут должны быть discounts - т.е. Many To Many связь,
    #  это потребует достаточно больших изменений, которые не разумно делать без тестов
    #  и с уже ограниченным временем
    discount: Mapped["Discount"] = relationship(back_populates="skus")

    items: Mapped[list["Item"]] = relationship("Item", back_populates='sku')


class ItemDiscountType(enum.StrEnum):
    BY_DEFECT = "BY_DEFECT"
    PROMOTION = "PROMOTION"


class ItemDiscount(database.Base):
    """Скидки, применимые к товару"""
    __tablename__ = "item_discounts"
    # TODO: Добавить констрейнт: если ItemDiscountType.PROMOTION, то discount_id is not null


    id: Mapped[uuid_pk]
    type: Mapped[ItemDiscountType]
    # Зарезервированная скидка либо за дефект, либо за акцию на момент создания заказа
    # TODO: Добавить ограничение - не более 100% или 99% и не меньше 0 или 1
    percentage: Mapped[int] = mapped_column(server_default=text("0"))

    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("items.id"))
    item: Mapped["Item"] = relationship("Item", back_populates="item_discounts")

    discount_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("discounts.id"))
    discount: Mapped["Discount"] = relationship("Discount", back_populates="item_discounts")


class Item(database.Base):
    """Товар"""
    __tablename__ = "items"

    id: Mapped[uuid_pk]
    sku_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skus.id"))
    sku: Mapped["Sku"] = relationship(back_populates="items")

    # TODO: А возможно тут и нужен Optional, чтобы была хотя какая-то полезная работа от process_acceptance?
    stock: Mapped["Stock"] = relationship("Stock", back_populates='item', uselist=False)

    posting_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("postings.id"))
    posting: Mapped["Posting"] = relationship("Posting", back_populates="items")

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="item")

    acceptance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("acceptances.id"))
    acceptance: Mapped["Acceptance"] = relationship("Acceptance", back_populates="items")

    item_discounts: Mapped[list["ItemDiscount"]] = relationship("ItemDiscount", back_populates="item")


class StockStatus(enum.StrEnum):
    # Валидный товар, который можно продавать пользователю
    VALID = "Valid"
    # Товар, который потеряли. В этот сток может попасть любая копия товара
    NOT_FOUND = "NotFound"
    # Уцененный товар, на который есть скидка
    DEFECT = "Defect"


class Stock(database.Base):
    """Описание состояния товара"""
    __tablename__ = "stocks"

    id: Mapped[uuid_pk]
    status: Mapped[StockStatus]
    is_reserved: Mapped[bool] = mapped_column(server_default=sql.false())

    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("items.id"))
    item: Mapped["Item"] = relationship(back_populates="stock")


# TODO: Возможно стоит сделать статус NEW и сделать его по умолчанию
class TaskStatus(enum.StrEnum):
    COMPLETED = "completed"
    IN_WORK = "in_work"
    CANCELED = "canceled"


class TaskType(enum.StrEnum):
    # Задача на размещение товара
    PLACING = "placing"
    # Задача на подбор товара.
    PICKING = "picking"


class Task(database.Base):
    """Определенная задача, в рамках которой надо совершить какое-то действие на складе/в логистике"""
    __tablename__ = "tasks"
    # TODO: Добавить констрейнт
    #  TaskType==PLACING and posting_id is not NULL
    #  or
    #  TaskType==PICKING and acceptance_id is not NULL

    # TODO: Добавить причину отмены?
    #  Так как она нигде не выводится и нам запрещено изменять контракт API,
    #  то в рамках поставленной задачи от подобного поля нет смысла
    id: Mapped[uuid_pk]
    status: Mapped[TaskStatus]
    created_at: Mapped[created_at]
    type: Mapped[TaskType]

    posting_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("postings.id"))
    posting: Mapped["Posting"] = relationship(back_populates="tasks")

    item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("items.id", use_alter=True))
    item: Mapped["Item"] = relationship(back_populates="tasks", uselist=False)

    acceptance_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("acceptances.id"))
    acceptance: Mapped["Acceptance"] = relationship("Acceptance", back_populates="tasks")


# TODO: Возможно стоит сделать статус NEW и сделать его по умолчанию
# TODO: Возможно стоит сделать статус ASSEMBLED перед статусом SENT, для просчета цены?
class PostingStatus(enum.StrEnum):
    IN_ITEM_PICK = "in_item_pick"
    SENT = "sent"
    CANCELED = "canceled"


class Posting(database.Base):
    __tablename__ = "postings"
    __table_args__ = (
        CheckConstraint("cost >= 0", name="cost_positive"),
    )

    id: Mapped[uuid_pk]
    status: Mapped[PostingStatus]
    created_at: Mapped[created_at]
    # TODO: Возможно стоит сделать значение по умолчанию?
    cost: Mapped[price]

    # TODO: Подумать делать ли отдельные relationship's с условиями?
    # valid_items
    # defect_items
    # not_found_items
    items: Mapped[list["Item"]] = relationship(back_populates="posting")

    tasks: Mapped[list["Task"]] = relationship(back_populates="posting")


class Acceptance(database.Base):
    __tablename__ = "acceptances"
    # TODO: Добавить ограничение в таблице acceptances на тип задач только PLACING
    # TODO: Теоретически есть намек на наличие статуса "выполнено" у приемки,
    #  который проставляется когда не осталось активных задач на размещение товара,
    #  (т.е. лучше всего это сделать в месте где обрабатываются задачи)
    #  но нигде в схемах этого нет, так что оставим проставление статуса на доработку/полировку,
    #  если останется время

    id: Mapped[uuid_pk]
    created_at: Mapped[created_at]
    items: Mapped[list["Item"]] = relationship(back_populates="acceptance")
    tasks: Mapped[list["Task"]] = relationship(back_populates="acceptance")
