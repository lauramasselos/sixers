# Webservices to support the robot

The robot will store the orders / map on the external web server, 
through this web server the cook will be able to see and modify current standing orders. 

Furthermore it should contain current map of the place in some representation easy to parse.


# Infrastructure:

Mostly based on [Digital ocean tutorial](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04).
Check [Django docs](https://docs.djangoproject.com/en/2.1/intro/) if you have never seen Django before and want to contribute.


# API

The API will accept and return JSON. There will be authentication using token stored on the robot. 

## GET /order

Returns list of all standing  orders. Each order has following properties:
- id of the order
- time of order
- table number
- product list


## POST /order

- Robot should use this when customer orders something. 
- Waitresses should use this (through the web interface) to instruct the robot to deliver some order

Parameters
- table: <int>
- products: List<int>

## POST /order/delivered/<order_id>
Marks the order as delivered

## GET /order/current

Returns details of the current order that the robot is delivering

## POST /order/currrent/<id>

This should be used primarily by the cook - after he puts products on the tray of the robot he has to tell the robot 
what order he put on the plate. 



# Map: (Optional)

