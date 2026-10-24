extends RefCounted

func _valid_receipt_result(path: String, result: Dictionary) -> bool:
	var item: Variant = result.get("item")
	if not item is Dictionary or not item.get("id") is String or str(item.id).is_empty():
		return false
	if path == "/cases/open":
		return _receipt_integer(result.get("roll"), 0, 9999) and result.get("table_version") is String and not str(result.table_version).is_empty()
	if not _receipt_integer(result.get("credits"), 0, 9007199254740991):
		return false
	return path == "/store/buy" or _receipt_integer(result.get("fee"), 0, 10000000)

func _receipt_integer(value: Variant, minimum: int, maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) == floor(float(value)) and float(value) >= minimum and float(value) <= maximum
