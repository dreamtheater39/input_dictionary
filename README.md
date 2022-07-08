# Dictionary Custom Component for Home Assitant
Dictionary custom component for Home Assistant

Download Latest release:
https://github.com/dreamtheater39/input_dictionary/releases/download/v0.1.0/input_dictionary.zip

Install by placing this in your 'config/custom_components/input_dictionary' Home Assistant folder

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

Here's another use case
1. Create a dictionary of rooms/areas in your house
2. Add each room/area as a key to the dictionary
3. The value of the room key can contain another dictionary object describing properties of the room such as (current_scene, occupancy, triggered_by, etc.)
4. Use these room properties to add more control to your automations! Example - turn off lights when no_motion only if it was turned on by motion in the first place etc. Restore a scene back to what it was earlier or refer to neighboring room scenes and set scene accordingly etc.
Here's a template example of reading from a dictionary object that's set as a value to a key

Set a dictionary as value
```
service: input_dictionary.append_dictionary
data:
  keyvalues: >-
    {"guest":'{"occupied":"true","scene":"bright","trigger":"motion
    triggered"}'}
target:
  entity_id: input_dictionary.dictionarytest
```
Get attributes from the dictionary using this template
```
{{ (state_attr('input_dictionary.dictionarytest', 'dictionary').guest|from_json).occupied }}
```



