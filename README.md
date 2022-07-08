# Dictionary Custom Component for Home Assitant
Dictionary custom component for Home Assistant

Download Latest release:
https://github.com/dreamtheater39/input_dictionary/releases/download/v0.1.0/input_dictionary.zip
Install by placing this in your config/custom_components/input_dictionary folder

Here's what it does -
1. Add a dictionary entity
2. Exposes 3 services - Append, Remove, Reset
3. Append - adds new key/values, modifies values if any keys already present
4. Remove - removes a key/value based on the key provided as input
5. Reset - clears the entire dictionary


Here's a configuration.yaml example
```
input_dictionary:
  global_dictionary:
    name: Global Dictionary
```
Example input for Append service call - 
```
service: input_dictionary.append_dictionary
data:
  keyvalues: '{"bedroom":"scene_relax", "guestroom":"scene_off"}'
target:
  entity_id: input_dictionary.global_dictionary
```
Example for a "condition trigger" to use one of these key/values in an automation
```
condition: template
value_template: >-
  {{ (state_attr('input_dictionary.global_dictionary', 'dictionary').bedroom) ==
  "scene_relax" }}
```
