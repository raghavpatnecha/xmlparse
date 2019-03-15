# xmlparse
Parsing xml for python

Given a xml the project should be able to generate an excel output which has all the pick rules, where they are attached , and what triggers them.

1. A pick rule is identified if it has `<ACTIONITEM SEQ="0" item="." max="1" min="0" qty="1"/>` inside RULE tag.

2. One of the RULE attribute "NAME" is attached at item or class tag, which means the rules is attached at this particular item/items.


What I am able to achieve till now is RULE tag identifiction and where it is attached. Still not able to figure out what triggers it.

Approach :

 a.) I extracted the RULE defination using AST ( Abstract Syntax Tree)
                   e.g RULE defination:
                                     RULE NAME :   `DefaultMeterForGovt
RULE DEF : (value(_amEntitled) = literal(1) and value(IsMeterSelected) != literal(yes) and (value(PB:PRICELIST) = literal(Y1) or value(PB:PRICELIST) = literal(Y2)))`


 b.) Point is each property e.g IsMeterSelected = yes is attched at an ITEM tag (or multiple tags). I need to replace that ITEM with property in rule definition. Lets say , for above rule definition it could be: 
                          `(ABC and XYZ) or (PQR)  # which will make it easier to understand that if these items are selected then the rule will trigger`


File Info:

1. sub_rule_prop_witem.py - > Gives all pick rule in xml, along with where they are attached(works fine). Although it gives what triggers them but fails to identify them correctly, as I have ignored the `or` `and` scenario and just manually checked the property


3. xml_ast_ruleparse.py - > Get all Rules definitions.



Few exceptions:

1. Properties like: `PB:PRICELIST`, `PB:SALES_TYPE`  can't be found at ITEMS. So can ignore them.

2.` _amEntitled` can also be ignored.

3. If you try to observe few of the RULES work in reverse order, like for all rules we will search like this :

   IsMeterSelected = value or
   IsMeterval > 5 

  Exception:
             `(propval(_sku) = value(PICK_SKU1)
                    or
              (propval(_sku) = value(PICK_SKU1)`

In the above scene the _sku is the "_sku" attrib of the item(_description is the _description of item) where RULE is attached at and PICK_SKU1 will be the property attached at some other item like in all cases. So we need to search PICK_SKU1 where it has the value of _sku(i.e where the rule is attached).

4. Another rule exception is:
          `(value(PICK_SKU1) = propval(._sku)`

Here it is not in reverse but the ._sku will th e '_sku' attrib attached at ITEM ; where the rule is attached
