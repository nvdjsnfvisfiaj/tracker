# Инструкция по настройке фильтров для коллекций NFT

Для каждой коллекции можно настроить фильтры по трем атрибутам:

- model: Фильтр по модели
- backdrop: Фильтр по фону
- symbol: Фильтр по символу

## Возможные значения:

- null: Без фильтрации (показывать все минты независимо от значения этого атрибута)
- "Название атрибута": Показывать только минты с указанным значением атрибута
- "Название1, Название2, Название3": Показывать минты с любым из указанных значений атрибута (перечисляются через
  запятую)

## Примеры настройки:

Показывать все минты RecordPlayer:

```json
"RecordPlayer": {
"model": null,
"backdrop": null,
"symbol": null
}
```

Показывать только RecordPlayer с черным фоном:

```json
"RecordPlayer": {
"model": null,
"backdrop": "Black",
"symbol": null
}
```

Показывать только DiamondRing с моделью Gold и символом Heart:

```json
"DiamondRing": {
"model": "Gold",
"backdrop": null,
"symbol": "Heart"
}
```

Показывать TopHat с несколькими моделями:

```json
"TopHat": {
"model": "Maestro, White Windsor, Black Raven",
"backdrop": null,
"symbol": null
}
```

Внимание! Названия атрибутов чувствительны к регистру и должны точно соответствовать названиям из
Telegram. https://t.me/GiftChangesModels
