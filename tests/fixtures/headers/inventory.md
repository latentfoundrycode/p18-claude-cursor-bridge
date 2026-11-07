---
record: inventory
header: 1
reflected_through: null
development_data: "Development data: none"
tables:
  features:
    columns: [Feature, What]
    key: Feature
  resources:
    columns: [Name, Kind]
    key: Name
  decisions:
    columns: [Decision, Reason]
    key: Decision
  deferred:
    columns: [Item, Why]
    key: Item
---
# fixture body
