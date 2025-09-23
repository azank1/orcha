The FoodTec POS supports a RESTful API that can accept orders from authenticated external sources, such
as catering or internet ordering systems validate and return them priced.
1. Overview
The Order Validation API is designed to have resource-oriented URLs (/validate/order, /validate/coupon, ... ) and to use HTTP error
codes to indicate various error types. All the messages including errors, are formatted in JSON.
1.1. Authentication
The Order Validation API v1 uses the Basic HTTP Auth protocol to authorize calls.
1.2. Registering API client
In order for a third-party application to be able to use the Order Validation API v1, it should first get registered with FoodTec POS.
Upon registration a client identifier (username) and client password will be issued to the third-party API client.
1.3. Error Handling
Invalid provided data can result into an error similar to the following:
Note that all these responses will have an HTTP 400 code with a customer error code in the meta object. The error and info fields
will always have the same value and the response object is going to be empty.
1.3.1. Authentication Failure Request Example
1.3.2. Authentication Failure Response Example
1.4. Error Codes
The values of words prefixed with a dollar sign ($) depend on the context of the error.
1.4.1. General Errors
Code Error/Info
1000 Unsupported order type. $message
1001 Not licensed for web
1002 ExternalRef cannot be empty or null
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
curl https://localhost/ws/store/v1/menu/ordertypes -i -H "Accept: application/json" -H "Content-Type: application/json"
BASH
HTTP/1.1 401 Unauthorized
Server: Apache-Coyote/1.
WWW-Authenticate: Basic realm="store services"
Content-Length: 0
Date: Mon, 16 Mar 2015 13:20:28 GMT
HTTP
Code Error/Info
1003 Open order for externalRef $externalRef already exists
1004 Unsupported order source: $orderSource. $message
1005 Cannot find order with externalRef: $externalRef
1007 $field1 is required when $field2 is present
1010 Order could not be placed
1011 Internal address error
1012 Order price cannot be calculated
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
1141 At least $cnt enforced ingredients is required for $category
$item $choice choice.
Code Error/Info
1150 Special name cannot be empty
1151 No such special $special
1152 Special $special must contain items
1153 The selling price for the special $special cannot be empty for
the special $special
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
1300 Address and zip fields must be specified for delivery orders
1301 Address or zip is missing
1303 Location not found
1304 Coordinates not found
1305 Did not find $field1 field corresponding to $field
1.4.5. Deferring & Date Errors
Code Error/Info
1400 $message
1401 Cannot set defer time for a past date: $deferDate
1402 Store is closed
Code Error/Info
1410 Cannot set defer time. Store will be closed on : $deferDate
1411 Cannot set defer time. Timeslot is full for the date: $deferDate
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
1561 Provided order tax $provided does not match calculated tax
$calculated
1562 Provided order discount $provided does not match calculated
discount $calculated
1563 Provided order delivery charge $provided does not match
calculated delivery charge $calculated
1.4.8. Coupon Application Errors
Code Error/Info
1600 No coupon matching the $code
1601 The coupon does not qualify for the order. $terms
1602 The coupon $code has been expired.
Code Error/Info
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
1.5. Order Object
This object defines an order object
Property Type Description
orderNum string The order numb
of the accepted
order. Returned
after acceptance
type enum The type of the
order. Allowed
values: Pickup,
Delivery. Requir
source enum The source of th
order. Allowed
values ( case
insensitive ): Doo
Dash, GrubHub,
Postmates, Uber
Eats, CyborgOps
Third Party.
Required
paid boolean Whether the ord
was paid. Requir
Property Type Description
isThirdPartyPickup boolean For Pickup orde
whether a third
party will pick t
order from the
store, instead of
the customer.
Optional
price float The total price o
the order
(including tax, ti
etc). Required
tax float The total order t
Optional
taxableSubtotal float The order’s taxa
subtotal. Option
tip float The order tip.
Optional
discount float The total order
discount. Option
deliveryCharge float The Delivery
charge if
applicable.
Optional
serviceCharge float The Service cha
if applicable.
Required when
serviceChargeNa
is present
serviceChargeName string The Service cha
name if applicab
Required when
serviceCharge is
present
timeOrdered date_time [^1
(https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#_footnotedef_1)]
The time that th
order has been
accepted. Return
after acceptance
deferTime date_time [^1
(https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#_footnotedef_1)]
If the order is to
deferred, this is
time at which th
order is due to t
customer. Optio
Property Type Description
promiseTime date_time [^1
(https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#_footnotedef_1)]
The time the ord
will be ready.
Returned after
acceptance
customer Customer
(https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#customer)
object
The order
customer details
Optional in Ord
Validation API
items Array of Item
(https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#item)
objects
The order items
Required if speci
are empty
specials Array of Special
(https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#special)
objects
The order specia
Required if items
are empty
adjustment Adjustment
(https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#adjustment)
object
The order
adjustment.
Optional
instructions string The order
instructions
provided by the
consumer. Max
characters allow
Optional
externalRef string Is a unique
identifier, provi
by the client. It i
used to prevent
duplicate orders
and to void the
order (if needed
via the Void Ord
endpoint. Requir
on acceptance A
only
Property Type Description
externalNumber string Is an identifier
which is provide
by the client for
orders from 3rd
party services su
as GrubHub tha
can be entered v
the Order
Acceptance API.
can be used whe
a customer calls
the store, the
employee will b
able to locate th
customer’s orde
1.5.1. Customer
This object defines a customer object
Property Type Description
name string The name of the customer. Required
phone string The customer’s phone, formatted as
AAA-XXX-NNNN. Optional
address string The street number and address ("123 W
Main St"). Optional
zip string The 5-digit zip code. Required when an
address is required
city string City. Optional
state string The 2-letter state. Optional
value1 string The apartment #, suite #, dorm name,
etc. Required when 'diff1' field is included
in the request
diff1 string This is what Value1 is. Required when
'value1' field is included in the request
value2 string Secondary location differentiator, e.g.
the room # within the dorm. Required
when 'diff2' field is included in the
request
diff2 string This is what Value2 is. Required when
'value2' field is included in the request
Property Type Description
latitude double Latitude. Required if store is configured
to accept customer coordinates
longitude double Longitude. Required if store is
configured to accept customer
coordinates
deliveryInstructions string Delivery instruction, if a Delivery order.
Optional
1.5.2. Item
This object defines an order item object
Property Type Description
category string The category
the item
belongs to
(such as
"Pizza").
Required
item string The name of
the item
within the
category (such
as "Chesse").
Required_
size string The size of the
item (such as
"Med").
Required
quantity integer The quantity
of the item.
Optional
(default: 1)
sellingPrice float The selling
price of the
item. Required
ingredients Array of Ingredient
(https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#ingredient)
objects
Items'
ingredients.
Optional
Property Type Description
externalRef string Is a unique
identifier,
provided by
the client for
identifying
items.
Optional
isInBucket boolean Indicates if
the item is
part of a
bucket.
Optional
1.5.3. Ingredient
This object defines an order item ingredient object
Property Type Description
ingredient string The name of the ingredient. Required
isLeftHalf boolean For a left-half ingredient. Optional
isRightHalf boolean For a right-half ingredient. Optional
ordered boolean A default ingredient that was de-
selected. Optional
isAdHoc boolean For an Ad-Hoc ingredient. Optional
price boolean The price for an Ad-Hoc ingredient.
Optional
1.5.4. Special
This object defines an order item special object
Property Type Description
special string The name of the
special or
coupon.
Required
type enum Allowed values
Special, Coupon.
Required
sellingPrice float The discounted
price of the
special or
coupon.
Required
Property Type Description
discount float The special or
coupon
discount.
Required
items Array of Item
(https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#item)
objects
The items that
this special or
coupon applies
to. Required
isCombo boolean Indicates if the
special is a
combo. Optional
couponCode string The coupon
code of the
special when
applied.
Optional
1.5.5. Adjustment
This object defines an order item adjustment object
Property Type Description
name string The name of the adjustment. Required
discount float The adjustment discount. Required
2. Endpoints
2.1. Order Validation
This call will validate an order and return it fully priced in the response. Any error identified will be returned as part of the
response. After the order gets successfully validated all items will get priced and the total price, tax, tip, discount and delivery
charge will be calculated. Items sent priced will be ignored and re-priced according to menu. Last any auto-apply special
matching the order will be applied.
URL /ws/store/v1/validate/order
HTTP Method POST
Available Since 9.
2.1.1. Example request
2.1.2. Example response
$ curl 'https://localhost/ws/store/v1/validate/order' -i -X POST -H 'Accept: application/json' -H 'Content-Type:
application/json' -d '{
"orderNum" : null,
"type" : "Pickup",
"source" : "Door Dash",
"price" : null,
"tax" : null,
"tip" : null,
"discount" : null,
"deliveryCharge" : null,
"deferTime" : null,
"customer" : {
"name" : "Foodtec Joe",
"phone" : "781-453-8620",
"address" : "175 Highland Avenue",
"zip" : "02494",
"city" : null,
"state" : "MA",
"value1" : "12G",
"diff1" : "Apt",
"value2" : null,
"diff2" : null,
"value3" : null,
"diff3" : null,
"latitude" : 0.0,
"longitude" : 0.0,
"deliveryInstructions" : "Take the stairs or elevator to the fourth floor"
},
"items" : [ {
"category" : "Pizza",
"item" : "Cheese",
"size" : "Sm.",
"quantity" : 3,
"sellingPrice" : 6.99,
"ingredients" : [],
"externalRef" : "fc0e2a1c-6020-4041-a2fd-1a5e42417aeb",
"isInBucket" : false
} ],
"specials" : [ ],
"payments" : [ ],
"orderTaker" : null,
"externalRef" : "d2257a43-c044-4dcb-bc44-012f4514e9a0"
}'
HTTP
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-
Content-Length: 1165

{
"orderNum": "0",
"source": "Door Dash",
"type": "Pickup",
"price": 22.55,
"tax": 1.58,
"taxableSubtotal": 20.97,
"tip": 0.0,
"discount": 0.0,
"deliveryCharge": 0.0,
"paymentFee": 0.0,
"timeOrdered": null,
"deferTime": null,
"customer": {
"name": "Foodtec Joe",
"phone": "781-453-8620",
"address": "175 Highland Avenue",
"zip": "02494",
"city": null,
"state": "MA",
"value1": "12G",
"diff1": "Apt",
"value2": null,
"diff2": null,
"value3": null,
"diff3": null,
"latitude": 0.0,
"longitude": 0.0,
"deliveryInstructions": "Take the stairs or elevator to the fourth floor"
},
"items": [
{
"category": "Pizza",
"item": "Cheese",
"size": "Sm.",
"quantity": 3 ,
"sellingPrice": 6.99,
"ingredients": [
{
"ingredient": "Original Crust",
"isLeftHalf": false,
"isRightHalf": false,
"ordered": true,
"qualifiers": []
},
{
"ingredient": "Pizza Sauce",
"isLeftHalf": false,
"isRightHalf": false,
"ordered": true,
"qualifiers": []
},
{
"ingredient": "Cheese",
"isLeftHalf": false,
"isRightHalf": false,
"ordered": true,
"qualifiers": []
}
],
"externalRef": "fc0e2a1c-6020-4041-a2fd-1a5e42417aeb",
"isInBucket": false
}
],
"specials": [],
"adjustment": null,
"paid": false,

HTTP
Example request(Drive thru)
Example response(Drive thru)
"isThirdPartyPickup": false,
"payments": [],
"orderTaker": null,
"externalRef": "d2257a43-c044-4dcb-bc44-012f4514e9a0",
"externalNumber": null
}
$ curl 'https://localhost/ws/store/v1/validate/order' -i -X POST -H 'Accept: application/json' -H 'Content-Type:
application/json' -d '{
"orderNum" : null,
"type" : "Drive Thru",
"source" : "Door Dash",
"price" : 27.39,
"tax" : 1.92,
"tip" : null,
"discount" : null,
"deliveryCharge" : null,
"deferTime" : null,
"customer" : {
"name" : "Foodtec Joe",
"phone" : "781-453-8620",
"address" : "175 Highland Avenue",
"zip" : "02494",
"city" : null,
"state" : "MA",
"value1" : "12G",
"diff1" : "Apt",
"value2" : null,
"diff2" : null,
"value3" : null,
"diff3" : null,
"latitude" : 0.0,
"longitude" : 0.0,
"deliveryInstructions" : "Take the stairs or elevator to the fourth floor"
},
"items" : [ {
"category" : "Pizza",
"item" : "Cheese",
"size" : "Sm.",
"quantity" : 3,
"sellingPrice" : 6.99,
"ingredients" : [ ],
"externalRef" : "fc0e2a1c-6020-4041-a2fd-1a5e42417aeb",
"isInBucket" : false
} ],
"specials" : [ ],
"payments" : [ ],
"orderTaker" : null,
"externalRef" : "d2257a43-c044-4dcb-bc44-012f4514e9a0"
}'
HTTP
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-
Content-Length: 1542

{
"orderNum": "0",
"source": "Door Dash",
"type": "Drive Thru",
"price": 22.55,
"tax": 1.58,
"taxableSubtotal": 20.97,
"tip": 0.0,
"discount": 0.0,
"deliveryCharge": 0.0,
"paymentFee": 0.0,
"timeOrdered": null,
"deferTime": null,
"customer": {
"name": "Foodtec Joe",
"phone": "781-453-8620",
"address": "175 Highland Avenue",
"zip": "02494",
"city": null,
"state": "MA",
"value1": "12G",
"diff1": "Apt",
"value2": null,
"diff2": null,
"value3": null,
"diff3": null,
"latitude": 0.0,
"longitude": 0.0,
"deliveryInstructions": "Take the stairs or elevator to the fourth floor"
},
"items": [
{
"category": "Pizza",
"item": "Cheese",
"size": "Sm.",
"quantity": 3 ,
"sellingPrice": 6.99,
"ingredients": [
{
"ingredient": "Original Crust",
"isLeftHalf": false,
"isRightHalf": false,
"ordered": true,
"qualifiers": []
},
{
"ingredient": "Pizza Sauce",
"isLeftHalf": false,
"isRightHalf": false,
"ordered": true,
"qualifiers": []
},
{
"ingredient": "Cheese",
"isLeftHalf": false,
"isRightHalf": false,
"ordered": true,
"qualifiers": []
}
],
"externalRef": "fc0e2a1c-6020-4041-a2fd-1a5e42417aeb",
"isInBucket": false
}
],
"specials": [],
"adjustment": null,
"paid": false,

HTTP
2.2. Coupon Validation
This call will try to apply the coupon as if it was actually added to the order. The order will be priced and returned in the response
object. Items sent priced will be ignored and re-priced according to menu.
URL /ws/store/v1/validate/coupon?code={couponCode}
HTTP Method POST
Available Since 9.
In the following example an order with two items is sent and a coupon named "testspe" is applied to the order. The "Test Special"
matches the given coupon code which is applied to one of the given items as can be seen in the returned object.
2.2.1. Example request
"isThirdPartyPickup": false,
"payments": [],
"orderTaker": null,
"externalRef": "d2257a43-c044-4dcb-bc44-012f4514e9a0",
"externalNumber": null
}
2.2.2. Example response
$ curl 'https://localhost/ws/store/v1/validate/coupon?code=testspe' -i -X POST -H 'Accept: application/json' -H 'Content-
Type: application/json' -d '{
"orderNum" : null,
"source" : "Cyborgs",
"type" : "Pickup",
"price" : null,
"tax" : null,
"tip" : null,
"discount" : null,
"taxableSubtotal": null,
"deliveryCharge" : null,
"deferTime" : null,
"customer" : {
"name" : "Foodtec Joe",
"phone" : "781-453-8620",
"address" : "175 Highland Avenue",
"zip" : "02494",
"city" : null,
"state" : "MA",
"value1" : "12G",
"diff1" : "Apt",
"value2" : null,
"diff2" : null,
"value3" : null,
"diff3" : null,
"latitude" : 0.0,
"longitude" : 0.0,
"deliveryInstructions" : "Take the stairs or elevator to the fourth floor"
},
"items" : [ {
"category" : "Pizza",
"item" : "Cheese",
"size" : "Sm.",
"quantity" : 3,
"sellingPrice" : 6.99,
"ingredients" : [ ],
"externalRef" : "e51d28fa-3dae-43ba-9b52-084515f7d79f",
"isInBucket" : false
} ],
"specials" : [ ],
"payments" : [ ],
"orderTaker" : null,
"externalRef" : "50627d47-43d9-48b3-b8a9-f57d449e973f"
}'
HTTP
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-
Content-Length: 1824

{
"orderNum": "0",
"source": "Cyborgs",
"type": "Pickup",
"price": 21.47,
"tax": 1.5,
"taxableSubtotal": 19.97,
"tip": 0.0,
"discount": 1.0,
"deliveryCharge": 0.0,
"paymentFee": 0.0,
"timeOrdered": null,
"deferTime": null,
"customer": {
"name": "Foodtec Joe",
"phone": "781-453-8620",
"address": "175 Highland Avenue",
"zip": "02494",
"city": null,
"state": "MA",
"value1": "12G",
"diff1": "Apt",
"value2": null,
"diff2": null,
"value3": null,
"diff3": null,
"latitude": 0.0,
"longitude": 0.0,
"deliveryInstructions": "Take the stairs or elevator to the fourth floor"
},
"items": [],
"specials": [
{
"special": "testspe",
"type": "Coupon",
"sellingPrice": 19.97,
"discount": 1.0,
"items": [
{
"category": "Pizza",
"item": "Cheese",
"size": "Sm.",
"quantity": 3 ,
"sellingPrice": 6.99,
"ingredients": [
{
"ingredient": "Original Crust",
"isLeftHalf": false,
"isRightHalf": false,
"ordered": true,
"qualifiers": []
},
{
"ingredient": "Pizza Sauce",
"isLeftHalf": false,
"isRightHalf": false,
"ordered": true,
"qualifiers": []
},
{
"ingredient": "Cheese",
"isLeftHalf": false,
"isRightHalf": false,
"ordered": true,
"qualifiers": []
}
],

HTTP
2.3. Store Employees Service
2.3.1. Validate Employee Server UniqueId
Validates if the UniqueId refers to an employee with who has the server role.
URL /ws/store/v1/validate/employees/server
HTTP Method GET
Available Since 9.
Example request
Example response
"externalRef": "e51d28fa-3dae-43ba-9b52-084515f7d79f",
"isInBucket": false,
"couponCode": "testspe"
}
],
"externalRef": null,
"isCombo": false
}
],
"adjustment": null,
"paid": false,
"isThirdPartyPickup": false,
"payments": [],
"orderTaker": null,
"externalRef": "50627d47-43d9-48b3-b8a9-f57d449e973f",
"externalNumber": null
}
$ curl 'https://localhost/ws/store/v1/validate/employees/server' -i -H 'Accept: application/json' -H 'Content-Type:
application/json'
BASH
HTTP/1.1 204 No Content
BASH
1 (https://docs.foodtecsolutions.com/pdirect/9.5/ads/doc/util/docspublic/OrderValidationApiV1.html#_footnoteref_1). date_time values are formatted in
milliseconds since January 1, 1970, 00:00:00 GMT
The information in this document is confidential and proprietary to FoodTec Solutions Inc. It may not be disclosed or distributed without prior
permission from FoodTec Solutions.