import re, regex
import logging
import json

intent = json.load(open("/home/vladislav/PycharmProjects/Nestlogic/Aiola/Task/Untitled (1)","r"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

builtin_slot_type_transformation = {
	"duration": "AMAZON.DURATION", "date": "AMAZON.DATE", "year": "AMAZON.DATE",
	"period_from": "AMAZON.DURATION","period_to": "AMAZON.DURATION",
	"date_period_from": "AMAZON.DATE", "date_period_to": "AMAZON.DATE",
	"time_period_from": "AMAZON.TIME", "time_period_to": "AMAZON.TIME",
	"date_from": "AMAZON.DATE", "date_to": "AMAZON.DATE",
	"time_from": "AMAZON.TIME", "time_to": "AMAZON.TIME", "time": "AMAZON.TIME",
	"number": "AMAZON.NUMBER", "percent": "AMAZON.Percentage"
}

expanding_parameters = {
	"time_period": ["time_period_from","time_period_to"], "period":["period_from","period_to"],
	"date_period": ["date_period_from","date_period_to"],
}

selector_slot_type_mapping = {"advertiser_or_brand_selector": ["advertiser","brand"]}

def types_name_forward_conversion(slot_type_name, environment_name, language=None, *args, **kwargs):

	if language is not None and language not in ("es", "en"):
		log.error(f"Language {language} doen't exist. Existing languages: es/en")
		return False

	prefix = language + environment_name if language else environment_name

	if slot_type_name is not None and not isinstance(slot_type_name, str):
		log.error(f"slot_type_name {slot_type_name} has valid value")
		raise False

	if slot_type_name in builtin_slot_type_transformation.keys():
		return (builtin_slot_type_transformation[slot_type_name], "AMAZON")
	else:
		return (prefix + slot_type_name, "CUSTOM")

def expanded_parameter_handler(parameter, *args, **kwargs):

	if parameter in expanding_parameters:
		return expanding_parameters[parameter]
	return False

def prefix_lex_fixer(word, *args, **kwargs):

	pattern = "lex_"

	return word.replace(pattern,"") if pattern in word else word


def slot_type_handler(slot_type, *args, **kwargs):

	if slot_type in builtin_slot_type_transformation:
		return (builtin_slot_type_transformation[slot_type],True)
	else :
		return (slot_type,False)

def parameters_to_model_parameters_conversion(intent, *args, **kwargs):

	intent_name_prefix = intent.get("name", None) + "_"
	intent_slots = intent.get("slots", None)
	model_parameters = { "slots": [] }

	for slot in intent_slots:

		slot_type = intent_slots[slot]["slot_type"]
		slot_name = intent_slots[slot]["name"]

		slot_mapping = intent_slots[slot]["mapping"] if "mapping" in intent_slots[slot] else \
													intent_slots[slot]["ontology_mapping"]
		default_value = intent_slots[slot]["default_value"]

		selector = True if len(slot_mapping) >= 2 else False

		if selector:
			for map_ in slot_mapping:
				d = dict()

				d["parameter_name"] = intent_name_prefix + prefix_lex_fixer(map_) + "_selector"
				d["slot_type"] = prefix_lex_fixer(map_)
				d["default_value"] = default_value
				model_parameters["slots"].append(d)
		#change after testing this block
		elif slot_type == "ontology_segmentation_criteria":
			model_parameters["slots"].append({
				"parameter_name": intent_name_prefix + prefix_lex_fixer(slot_name),
				"slot_type" : prefix_lex_fixer(slot_mapping[0]),
				"default_value": default_value

			})
			log.info("Ontology_segmentation_criteria added")

		else:

			expanded = expanded_parameter_handler(prefix_lex_fixer(slot_name))

			if expanded:
				parameter_names = expanded
				slot_types = [builtin_slot_type_transformation[p] for p in parameter_names]

				for parameter_name,slot_type_ in zip(parameter_names,slot_types):
					model_parameters["slots"].append( {
						"parameter_name": intent_name_prefix + parameter_name,
						"slot_type": slot_type_,
						"default_value": {"from": None} if parameter_name.endswith("from") else {"to":None}
					} 
					)

			else:
				slot_type_,model_builtin = slot_type_handler(slot_type)
				parameter_name = intent_name_prefix + prefix_lex_fixer(slot_name)
				d = {"parameter_name": parameter_name,
					 "slot_type": slot_type_,
					 "default_value": default_value
				}
				if model_builtin:
					d["model_builtin"] = True

				model_parameters["slots"].append(d)

	intent["model_parameters"] = model_parameters
	log.info("Status : OK!")

	return intent

def test(intent):
	print("---------------------------------")
	intent = parameters_to_model_parameters_conversion(intent)
	json.dump(intent,open("output.json","w"),indent = 4)
test(intent)