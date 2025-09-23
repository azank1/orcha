The FoodTec POS supports a RESTful API that exports the menu items.
1. Overview
The Menu Export API is designed to have resource-oriented URLs (/categories, /items, ... ) and to use HTTP error codes to
indicate various error types. All the messages including errors, are formatted in JSON.
1.1. Authentication
The Menu Export API v1 uses the Basic HTTP Auth protocol to authorize calls.
1.2. Registering API client
In order for a third-party application to be able to use the Menu Export API v1, it should first get registered with FoodTec
POS. Upon registration a client identifier (username) and client password will be issued to the third-party API client.
1.3. Error Handling
Invalid provided data can result into an error similar to the following:
Note that all these responses will have an HTTP 400 code with a customer error code in the meta object. The error and info
fields will always have the same value and the response object is going to be empty.
1.3.1. Authentication Failure Request Example
1.3.2. Authentication Failure Response Example
1.4. Error Codes
The values of words prefixed with a dollar sign ($) depend on the context of the error.
1.4.1. General Errors
Code Error/Info
1000 Unsupported order type. $message
1001 Not licensed for web
1002 ExternalRef cannot be empty or null
1003 Open order for externalRef $externalRef already exists
1004 Unsupported order source: $orderSource. $message
1005 Cannot find order with externalRef: $externalRef
1007 $field1 is required when $field2 is present
1010 Order could not be placed
1011 Internal address error
1012 Order price cannot be calculated
HTTP/1.1 400 Bad Request
Content-Type: application/json;charset=UTF-
{
"meta": {
"code": 1600,
"error": "No coupon matching the 3dolloff",
"info": "No coupon matching the 3dolloff"
},
"response": ""
}
HTTP
curl https://localhost/ws/store/v1/menu/ordertypes -i -H "Accept: application/json" -H "Content-Type:
application/json"
BASH
HTTP/1.1 401 Unauthorized
Server: Apache-Coyote/1.
WWW-Authenticate: Basic realm="store services"
Content-Length: 0
Date: Mon, 16 Mar 2015 13:20:28 GMT
HTTP
Code Error/Info
1020 Cannot calculate price for item $item ($category)
1021 Cannot calculate price for special $special
1022 Cannot calculate discount for special $special
1050 $order_could_not_be_voided_reason
1.4.2. Menu Errors
Code Error/Info
1100 At least one item or special must be specified
1101 Category cannot be empty
1102 No such category $category
1110 Item cannot be empty
1111 No such item $item for category $category
1120 Item size cannot be empty for item $item ($category)
1121 No such size $size for item $item ($category)
1122 The size $size is not available for item $item ($category)
1123 The item $item ($category) is out of stock
1124 Item $item contains an ingredient with empty name
1125 $invalid_ingredient_name_reason
1130 No such ingredient $ingredient for item $item ($category)
1131 No such qualifier $qualifier for item $item ($category)
1140 Quantity must be positive for item $item ($category)
1141 At least $cnt enforced ingredients is required for
$category $item $choice choice.
1150 Special name cannot be empty
1151 No such special $special
1152 Special $special must contain items
Code Error/Info
1153 The selling price for the special $special cannot be empty
for the special $special
1154 The selling price $price for the special $special is invalid
1155 The discount for the special $special cannot be empty
1156 The discount $discount for the special $special is invalid
1157 Unsupported special type. $message
1158 Unsatisfied special $message
1159 The $special is limited to $max per order.
1.4.3. Customer Errors
Code Error/Info
1200 Customer cannot be null
1210 The name of the customer must be specified
1220 The phone of the customer must be specified
1221 Invalid customer phone $phone. $message
1.4.4. Delivery address Errors
Code Error/Info
1300 Address and zip fields must be specified for delivery
orders
1301 Address or zip is missing
1303 Location not found
1304 Coordinates not found
1305 Did not find $field1 field corresponding to $field
1.4.5. Deferring & Date Errors
Code Error/Info
1400 $message
1401 Cannot set defer time for a past date: $deferDate
Code Error/Info
1402 Store is closed
1410 Cannot set defer time. Store will be closed on : $deferDate
1411 Cannot set defer time. Timeslot is full for the date:
$deferDate
1420 $message
1.4.6. Pricing Errors
Code Error/Info
1506 Invalid order price $price
1507 Invalid order tax $tax
1508 Invalid order tip $tip
1509 Invalid order discout $discount
1510 Invalid order delivery charge $charge
1511 Invalid price $price for item $item
1512 Order Price cannot be empty
1513 The selling price for item $item cannot be empty
1514 The price for ad-hoc $ingredient cannot be empty
1515 Invalid Service Charge price $price
1.4.7. Pricing Mismatches
Code Error/Info
1560 Provided order price $provided does not match calculated
price $calculated
1561 Provided order tax $provided does not match calculated
tax $calculated
1562 Provided order discount $provided does not match
calculated discount $calculated
1563 Provided order delivery charge $provided does not match
calculated delivery charge $calculated
1.4.8. Coupon Application Errors
Code Error/Info
1600 No coupon matching the $code
1601 The coupon does not qualify for the order. $terms
1602 The coupon $code has been expired.
1603 The coupon $code has been already used.
1604 The coupon $code cannot be applied.
1605 The coupon $code cannot be matched with this special.
1606 $coupon_redemption_failed_reason.
1607 Cannot apply $code, one adjustment per order allowed.
1.4.9. Adjustment Application Errors
Code Error/Info
1190 Adjustment name cannot be empty
1191 Adjustment discount cannot be empty
1192 Invalid adjustment discount $discount
2. Resources
2.1. Order Types
Returns the list of available order types.
URL /ws/store/v1/menu/ordertypes
HTTP Method GET
Available Since 9.
2.1.1. Example request
2.1.2. Example response
$ curl 'https://localhost/ws/store/v1/menu/ordertypes' -i -H 'Accept: application/json' -H 'Content-Type:
application/json'
HTTP
2.2. Menu Categories
2.2.1. Get all menu categories
Returns a list of all menu categories available. Each category will also include all the items belonging to it.
URL /ws/store/v1/menu/categories?orderType={orderType}
HTTP Method GET
Available Since 9.
2.2.2. Example request
2.2.3. Example response
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-
[ {
"orderType" : "delivery",
"requiresAddress" : true
}, {
"orderType" : "pickup",
"requiresAddress" : false
} ]
HTTP
$ curl 'https://localhost/ws/store/v1/menu/categories?orderType=delivery' -i -H 'Accept: application/json' -H
'Content-Type: application/json'
HTTP
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-

[ {
"category" : "Pizza",
"items" : [ {
"item" : "BBQ Chicken",
"code": "15963285741",
"sizePrices" : [ {
"size" : "10",
"price" : 11.
}, {
"size" : "12",
"price" : 15.
}, {
"size" : "14",
"price" : 19.
}, {
"size" : "16",
"price" : 22.
}, {
"size" : "18",
"price" : 25.
} ],
"choices" : [ {
"choice" : "Toppinngs",
"enforcedIngredients" : 0 ,
"ingredients" : [ {
"ingredient" : "Cheese",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Cheddar Cheese",
"sizePrices" : [ {
"size" : "12",
"price" : 1.

HTTP
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Chicken",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
} ],
"dependsOn":null
}, {
"choice" : "Crusts",
"enforcedIngredients" : 0 ,
"ingredients" : [ {

"ingredient" : "Regular Crust",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Thin Crust",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Thick Crust",

2.2.4. Get a specific menu category
Returns the menu category requested. Category will also include all the items belonging to that category.
URL /ws/store/v1/menu/categories/{categoryName}?
orderType={orderType}
HTTP Method GET
Available Since 9.
2.2.5. Example request
2.2.6. Example response
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
} ],
"dependsOn":null
} ]
} ]
} ]
$ curl 'https://localhost/ws/store/v1/menu/categories/Pizza?orderType=delivery' -i -H 'Accept: application/json' -
H 'Content-Type: application/json'
HTTP
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-

{
"category" : "Pizza",
"items" : [ {
"item" : "BBQ Chicken",
"code": "15963285741",
"sizePrices" : [ {
"size" : "10",
"price" : 11.
}, {
"size" : "12",
"price" : 15.
}, {
"size" : "14",
"price" : 19.
}, {
"size" : "16",
"price" : 22.
}, {
"size" : "18",
"price" : 25.
} ],
"choices" : [ {
"choice" : "Toppinngs",
"enforcedIngredients" : 0 ,
"ingredients" : [ {
"ingredient" : "Cheese",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Cheddar Cheese",
"sizePrices" : [ {
"size" : "12",
"price" : 1.

HTTP
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Chicken",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
} ],
"dependsOn":"Side House Salad"
}, {
"choice" : "Crusts",
"enforcedIngredients" : 0 ,
"ingredients" : [ {

"ingredient" : "Regular Crust",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Thin Crust",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Thick Crust",

2.2.7. Invalid request Example
2.2.8. Invalid Response Example
2.3. Menu Items
2.3.1. Get non available items
Return the items for the requested category and order type, that are not currently available on the menu.
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
} ],
"dependsOn":"Side House Salad"
} ]
} ]
}
$ curl 'https://localhost/ws/store/v1/menu/categories/unknown%20category?orderType=delivery' -i -H "Accept:
application/json" -H "Content-Type: application/json"
BASH
HTTP/1.1 400 Bad Request
Content-Type: application/json;charset=UTF-
{
"meta":{
"code": 1102 ,
"error":"No such category unknown category",
"info":"No such category unknown category"
},
"response":""
}
HTTP
URL /ws/store/v1/menu/categories/{categoryName}/items?
orderType={orderType}&available=false
HTTP Method GET
Available Since 9.
2.3.2. Example request
2.3.3. Example response
$ curl 'https://localhost/ws/store/v1/menu/categories/Pizza/items?orderType=delivery&available=false' -i -H
'Accept: application/json' -H 'Content-Type: application/json'
HTTP
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-

[ {
"item" : "Hawaiian",
"code": "15963285741",
"sizePrices" : [ {
"size" : "10",
"price" : 11.
}, {
"size" : "12",
"price" : 15.
}, {
"size" : "14",
"price" : 19.
}, {
"size" : "16",
"price" : 22.
}, {
"size" : "18",
"price" : 25.
} ],
"choices" : [ {
"choice" : "Toppinngs",
"enforcedIngredients" : 0 ,
"ingredients" : [ {
"ingredient" : "Cheese",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Cheddar Cheese",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",

HTTP
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Chicken",
"sizePrices" : [ {
"size" : "12",
"price" : 1.
}, {
"size" : "14",
"price" : 2.
}, {
"size" : "16",
"price" : 2.
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
} ],
"dependsOn":null
}, {
"choice" : "Crusts",
"enforcedIngredients" : 0 ,
"ingredients" : [ {
"ingredient" : "Regular Crust",
"sizePrices" : [ {

"size" : "12",
"price" : 1.5
}, {
"size" : "14",
"price" : 2.0
}, {
"size" : "16",
"price" : 2.2
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Thin Crust",
"sizePrices" : [ {
"size" : "12",
"price" : 1.5
}, {
"size" : "14",
"price" : 2.0
}, {
"size" : "16",
"price" : 2.2
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Thick Crust",
"sizePrices" : [ {
"size" : "12",

2.3.4. Get a specific menu item
Return the item for the requested category, item and order type.
URL /ws/store/v1/menu/categories/{categoryName}/items/{itemName}?
orderType={orderType}
HTTP Method GET
Available Since 9.1
2.3.5. Example request
2.3.6. Example response
"price" : 1.5
}, {
"size" : "14",
"price" : 2.0
}, {
"size" : "16",
"price" : 2.2
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
} ],
"dependsOn":"Mushrooms"
} ]
} ]
$ curl 'https://localhost/ws/store/v1/menu/categories/Pizza/items/BBQ%20Chicken?orderType=delivery' -i -H 'Accept:
application/json' -H 'Content-Type: application/json'
HTTP
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
"item" : "BBQ Chicken",
"code": "15963285741",
"sizePrices" : [ {
"size" : "10",
"price" : 11.95
}, {
"size" : "12",
"price" : 15.95
}, {
"size" : "14",
"price" : 19.95
}, {
"size" : "16",
"price" : 22.95
}, {
"size" : "18",
"price" : 25.95
} ],
"choices" : [ {
"choice" : "Toppinngs",
"enforcedIngredients" : 0 ,
"ingredients" : [ {
"ingredient" : "Cheese",
"sizePrices" : [ {
"size" : "12",
"price" : 1.5
}, {
"size" : "14",
"price" : 2.0
}, {
"size" : "16",
"price" : 2.2
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Cheddar Cheese",
"sizePrices" : [ {
"size" : "12",
"price" : 1.5
}, {
"size" : "14",

HTTP
"price" : 2.0
}, {
"size" : "16",
"price" : 2.2
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Chicken",
"sizePrices" : [ {
"size" : "12",
"price" : 1.5
}, {
"size" : "14",
"price" : 2.0
}, {
"size" : "16",
"price" : 2.2
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
} ],
"dependsOn":null
}, {
"choice" : "Crusts",
"enforcedIngredients" : 0 ,
"ingredients" : [ {
"ingredient" : "Regular Crust",
"sizePrices" : [ {

"size" : "12",
"price" : 1.5
}, {
"size" : "14",
"price" : 2.0
}, {
"size" : "16",
"price" : 2.2
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Thin Crust",
"sizePrices" : [ {
"size" : "12",
"price" : 1.5
}, {
"size" : "14",
"price" : 2.0
}, {
"size" : "16",
"price" : 2.2
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
}, {
"ingredient" : "Thick Crust",
"sizePrices" : [ {
"size" : "12",

2.4. Menu Specials
2.4.1. Get all menu specials
Returns a list of all menu specials available for the requested orderType.
URL /ws/store/v1/menu/specials?orderType={orderType}
HTTP Method GET
Available Since 9.1
2.4.2. Example request
2.4.3. Example response
"price" : 1.5
}, {
"size" : "14",
"price" : 2.0
}, {
"size" : "16",
"price" : 2.2
} ],
"allowHalfs" : false,
"isDefault" : true,
"qualifiers" : [ {
"name" : "Light",
"priceFactor" : 0.0,
"recipeFactor" : 0.0,
"isDefault" : true
}, {
"name" : "Extra",
"priceFactor" : 1.0,
"recipeFactor" : 1.0,
"isDefault" : false
}, {
"name" : "XXtra",
"priceFactor" : 2.0,
"recipeFactor" : 2.0,
"isDefault" : false
} ],
"code": null
} ],
"dependsOn":null
} ]
}
$ curl 'https://localhost/ws/store/v1/menu/specials?orderType=delivery' -i -H 'Accept: application/json' -H
'Content-Type: application/json'
HTTP
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

[ {
"special" : "$5.00 Off Any Order $25.00",
"label" : null,
"description" : null,
"type" : "Special",
"disclaimer" : null,
"start" : null,
"end" : null,
"orderTypes" : [ "Delivery", "Pickup" ],
"code": "5OFFANY25",
"isCombo": false
} ]

HTTP
The information in this document is confidential and proprietary to FoodTec Solutions Inc. It may not be disclosed or distributed
without prior permission from FoodTec Solutions.