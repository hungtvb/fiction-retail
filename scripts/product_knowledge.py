"""Purpose-written, *fictional* product knowledge for bounded retrieval exercises.

Every entry represents a designed training scenario, not a real SKU/manufacturer claim.
Facts remain constrained to the parent catalog's simulated specifications.
"""
from __future__ import annotations

# Each row: intended use, fit/selection guidance, care/handling, notable limitations,
# three product-specific customer questions and grounded answers.
DETAILS = {
'Wireless Earbuds': (
 'Portable stereo listening and voice audio from a Bluetooth-capable source.',
 'Pair with a Bluetooth source; verify the source supports the desired audio and microphone behavior. USB-C is the charging connector, not a wired audio input.',
 'Keep charging contacts clean and dry; recharge through a suitable USB-C supply before diagnosing pairing failures.',
 'No rated battery runtime, water-resistance class, active noise cancellation, or multipoint pairing is documented.',
 [('Can I connect these using only a USB-C cable?', 'No wired USB-C audio mode is specified; USB-C is documented for charging. Use a Bluetooth source for audio.'),('Why do the earbuds not appear when searching for Bluetooth devices?', 'Check that the earbuds have charge and are available for pairing, then repeat Bluetooth discovery on the source device. The exact reset sequence is not documented.'),('Are these suitable for swimming or rain?', 'No IP water-resistance rating is provided; water exposure cannot be recommended.')]),
'Portable Speaker': (
 'Portable playback from a Bluetooth audio source for casual indoor listening.',
 'Pair with a Bluetooth-capable player; its quoted 10-hour playback figure is a listed rating, not a guarantee at every volume.',
 'Charge by USB-C; avoid covering openings and store away from moisture until a protection rating is established.',
 'No microphone, waterproof certification, auxiliary input or stereo-link feature is documented.',
 [('How long can the speaker play?', 'The specification lists a rated playback time of 10 hours; actual performance at high volume is not established.'),('Can two speakers connect as a stereo pair?', 'Stereo pairing is not documented for this model.'),('Does it support a wired AUX connection?', 'Only Bluetooth input is described; an AUX port is not specified.')]),
'USB-C Hub': (
 'Expand a supported USB-C computer with four USB ports and one HDMI output.',
 'For HDMI use, the host USB-C port must itself support video output; having a USB-C connector alone is insufficient.',
 'Connect directly to a compatible host; use a suitable USB-C power source if supplying passthrough power.',
 'The 60 W passthrough rating is not the same as guaranteed laptop charging. Supported HDMI resolution and USB data rates are not supplied.',
 [('Why is there no HDMI image?', 'Confirm that the host USB-C port can send video, then verify the display input and cable. The hub cannot add video capability to a data-only port.'),('Will 60 W passthrough charge every laptop?', 'No. It is a stated passthrough limit, not a compatibility or power-delivery guarantee for any specific laptop.'),('How many USB peripheral ports are available?', 'Four USB ports are listed, plus one HDMI output; their individual speed classes are unspecified.')]),
'Laptop Sleeve': (
 'Padded protective carry sleeve for a laptop in the nominal 13-inch form-factor range.',
 'Measure the actual device body, including thick protective cases; the 13-inch label alone does not establish precise external fit.',
 'Wipe the polyester shell and let the sleeve dry completely before storing electronics.',
 'Not a hard impact case and not documented as waterproof or certified for drops.',
 [('Will every 13-inch laptop fit?', 'Not guaranteed: device dimensions and sleeve interior dimensions must be checked; exact internal dimensions are not provided.'),('Can I carry a wet laptop in it?', 'No moisture-proof protection is documented. Keep both sleeve and electronics dry.'),('Does it replace a hard case for drops?', 'No certified drop protection is stated; the sleeve offers a padded compartment only.')]),
'Wireless Charging Pad': (
 'Desk charger for devices that support Qi wireless charging.',
 'Verify the receiving device supports Qi wireless charging and that the USB-C adapter can supply suitable power; a charger plug is not included.',
 'Place the compatible device centered on the pad and keep the pad dry and clear of metal objects.',
 'Charging power in watts, magnetic alignment, fast-charge classes and bundled wall adapter are not specified.',
 [('Will it charge a phone without Qi?', 'No. A compatible Qi-enabled receiver is required.'),('Is a wall charger included?', 'No. The stated specification excludes a power supply.'),('What is the maximum charging wattage?', 'A wattage figure is not provided, so a specific fast-charge speed cannot be confirmed.')]),
'Everyday Cotton T-Shirt': (
 'Everyday casual shirt with a regular-fit silhouette and a 100% cotton fabric specification.',
 'Use a garment measurement chart to choose sizing; the product size information does not include chest, length or shrinkage measurements.',
 'Machine wash cold and follow garment care-label instructions; tumble-dryer suitability is not specified.',
 'No UV protection, flame-resistance, stretch percentage or colorfastness rating is documented.',
 [('Is the fit slim or loose?', 'The shirt has a regular fit, not a slim fit; consult the garment chart for measurements.'),('Can it be washed in warm water?', 'The documented care instruction is machine wash cold. Warm-water suitability is not established.'),('Is the fabric a cotton blend?', 'No; the fabric specification is 100% cotton.')]),
'Lightweight Hoodie': (
 'Casual light layering with a hood and drawstring for everyday wear.',
 'Use the specific garment chart rather than guessing from a familiar brand size.',
 'Machine wash cold; inspect the drawstring and seams after washing.',
 'Exact cotton-blend ratio, thermal rating and water resistance are not specified.',
 [('Is it 100% cotton?', 'No. It is described as a cotton blend; the fiber percentages are not provided.'),('Will it keep me dry in rain?', 'There is no waterproof specification for this hoodie.'),('How do I choose a size for layering?', 'Refer to garment measurements; a numeric allowance for layered clothing is not documented.')]),
'Travel Jacket': (
 'Light outer layer with a nylon shell, zipper front and wind-resistant finish.',
 'Suitable for general wind protection; select sizing based on outerwear measurements and planned layers.',
 'Follow the garment label for cleaning; do not assume high-temperature drying is safe for its finish.',
 'Wind resistance must not be confused with waterproof certification or a cold-weather temperature rating.',
 [('Is the jacket waterproof?', 'No waterproof rating or sealed-seam construction is documented.'),('Is it insulated for winter?', 'No insulation or temperature rating is specified.'),('What is the main shell material?', 'The outer shell is nylon.')]),
'Relaxed Fit Chinos': (
 'Casual cotton-twill trousers with a relaxed cut.',
 'Choose size using both waist and inseam measurements; relaxed fit describes the cut, not guaranteed sizing.',
 'Machine wash cold; review the care label before drying or ironing.',
 'No stretch percentage, stain resistance or preshrink treatment is provided.',
 [('Are these slim-fit trousers?', 'No. The specified fit is relaxed.'),('How can I choose the correct length?', 'Use the inseam measurement; the product data does not list a universal inseam for all sizes.'),('Do these have elastic stretch?', 'Stretch content is not specified; do not assume an elastane blend.')]),
'Everyday Polo Shirt': (
 'Casual cotton-knit, short-sleeved polo shirt for everyday wear.',
 'Check collar, chest and garment-length measurements rather than using a generic letter size.',
 'Machine wash cold and follow the garment care instructions.',
 'No exact cotton weight, shrinkage tolerance or sports-performance treatment is described.',
 [('Is this a long-sleeved shirt?', 'No. The specification says short sleeves.'),('Can I tumble-dry it on high heat?', 'Only cold-machine-wash guidance is documented; high-heat drying suitability is unknown.'),('What fabric does it use?', 'Cotton knit is specified; exact fabric weight is not provided.')]),
'Practical Photography Handbook': (
 'Illustrated, English-language printed introduction to practical photography concepts.',
 'Choose it for a physical reading reference; there is no advertised digital copy or camera-specific firmware coverage.',
 'Keep the paperback dry and avoid bending the binding.',
 'No included ebook, video course, professional certification or device-specific compatibility is claimed.',
 [('Is there an ebook included?', 'No electronic edition is included with this paperback.'),('Does it include illustrations?', 'Yes, illustrated chapters are specified.'),('Is it written in Vietnamese?', 'No. The specified language is English.')]),
'Everyday Cooking Guide': (
 'English-language paperback with illustrated recipes for home cooking practice.',
 'Use ingredients and allergen labels appropriate to the person eating; the guide is not a dietary suitability certification.',
 'Protect the printed pages from liquids and heat during kitchen use.',
 'Nutritional, medical and allergen-free guarantees are not provided.',
 [('Is this a digital recipe subscription?', 'No. It is a paperback with no digital access specified.'),('Are all recipes safe for nut allergies?', 'No allergy suitability guarantee is available; each ingredient must be evaluated separately.'),('Is the book illustrated?', 'Yes, recipe illustrations are explicitly listed.')]),
'Introduction to Data Analysis': (
 'Printed, English-language introductory reference featuring worked examples.',
 'Useful for reading examples on paper; check course requirements separately if a specific software package is required.',
 'Keep the paperback away from moisture; annotate with removable notes if needed.',
 'There is no bundled online platform, code repository, software license or accreditation.',
 [('Is access to an online course included?', 'No digital course access is included.'),('Does the book show worked examples?', 'Yes, worked examples are part of the described content.'),('Which programming language is used?', 'No specific language is identified in the supplied product information.')]),
'Urban Gardening Guide': (
 'Illustrated, English-language paperback for general urban gardening reading.',
 'Verify planting dates and plant suitability against the local climate and regional advice.',
 'Store printed pages in a dry place away from soil and water.',
 'The book is not a source of local regulation, climate certification or guaranteed crop outcomes.',
 [('Will the planting schedule work in every city?', 'No. Regional planting advice may vary and should be checked locally.'),('Are photographs included?', 'The book includes full-color photographs.'),('Is an app included?', 'No bundled app or digital format is documented.')]),
'Ceramic Coffee Mug': (
 'Reusable ceramic beverage mug with a nominal 350 mL capacity.',
 'Use for ordinary drinks while leaving headroom; 350 mL is nominal, not a guarantee for every fill condition.',
 'Hand wash as recommended; inspect for chips and cracking before reuse.',
 'Microwave, oven and dishwasher ratings are absent; do not assume any of those uses are safe.',
 [('Can I microwave it?', 'Microwave safety is not certified in the available specification.'),('What is the capacity?', 'The stated nominal capacity is 350 mL.'),('Is it dishwasher-safe?', 'Hand washing is recommended; dishwasher certification is not provided.')]),
'Cotton Throw Blanket': (
 'Indoor cotton textile throw, specified as 130 × 170 cm.',
 'Compare the stated dimensions with the desired couch or chair coverage; this is not a mattress-size label.',
 'Machine wash cold and follow garment care-label instructions.',
 'There is no outdoor weatherproof, fire-resistance or shrinkage-performance claim.',
 [('How large is the throw?', 'The throw measures 130 by 170 centimeters.'),('Can I leave it outdoors?', 'It is specified as an indoor home textile; weather resistance is not established.'),('Can it be machine-washed?', 'Yes, cold machine wash is listed.')]),
'LED Desk Lamp': (
 'Compact indoor task lighting using a nominal 5 W LED and USB power.',
 'Connect to a compatible 5 V USB power supply; the USB connector is for power, not data connectivity.',
 'Unplug before cleaning and avoid moisture near the connector.',
 'Brightness in lumens, replaceability, battery backup, color temperature and dimming are unspecified.',
 [('Can this run from a USB power supply?', 'Yes. The lamp uses a 5 V USB power input.'),('How bright is it?', 'Only nominal electrical power (5 W) is given; lumens are not stated.'),('Does it have a rechargeable battery?', 'No battery is documented, so battery-powered operation cannot be assumed.')]),
'Kitchen Storage Set': (
 'Three BPA-free plastic containers for ordinary kitchen storage.',
 'Select storage contents according to container suitability; no airtight, freezer or microwave rating is documented.',
 'Hand wash the containers; do not place them in an oven.',
 'A BPA-free material statement does not establish oven, microwave, dishwasher or food-temperature limits.',
 [('How many containers are included?', 'Three containers are listed.'),('Can I bake food in them?', 'No oven certification is provided; do not use them for baking.'),('Are they safe for the dishwasher?', 'Hand washing is the documented care recommendation.')]),
'Gentle Face Cleanser': (
 'Fragrance-free, external-use facial cleansing product in a 200 mL container.',
 'Use as directed on the product label and discontinue use if irritation occurs; patch-test when appropriate.',
 'Close the package after use and avoid contact with eyes unless labeling explicitly permits.',
 'No medical efficacy, treatment claim, complete ingredient list or suitability for all skin types is available.',
 [('How much cleanser is included?', 'The bottle contains 200 mL.'),('Does it contain added fragrance?', 'It is described as fragrance free; the full ingredient list is not supplied.'),('Will it treat acne or eczema?', 'No treatment efficacy data is provided; medical claims cannot be inferred.')]),
'Daily Moisturizer': (
 'Glycerin-based external-use moisturizing cream in a 50 mL container.',
 'Follow the package directions and check individual skin tolerance before regular use.',
 'Keep the container closed and avoid eye contact.',
 'No SPF protection, clinical results, complete formula or hypoallergenic certification is specified.',
 [('Does it include sunscreen?', 'No SPF value or UV protection claim is documented.'),('What is the main described base?', 'The product contains a glycerin-based formula.'),('Is it guaranteed to suit sensitive skin?', 'No. Skin suitability varies and no hypoallergenic certification is provided.')]),
'Hair Conditioning Mask': (
 'Rinse-out hair conditioning treatment in a 250 mL pack.',
 'Apply only as the product label directs and rinse thoroughly; the formula is not described as leave-in.',
 'Close the container after use and avoid unintended eye contact.',
 'No documented color-safety guarantee, clinical repair claims or exact ingredient formula.',
 [('Should I leave this product in my hair?', 'No. This product is a rinse-out treatment.'),('What is the container size?', '250 mL.'),('Is it safe for color-treated hair?', 'Color-treated suitability is not documented; check the detailed label before recommending.')]),
'Hand Cream': (
 'Glycerin-based external-use hand moisturizer in a 75 mL tube.',
 'Patch test if the user is concerned about skin sensitivity and follow package instructions.',
 'Store closed and avoid using on damaged skin without appropriate professional advice.',
 'No medical treatment or complete ingredient list is available.',
 [('How large is the tube?', '75 mL.'),('Is the cream fragrance free?', 'No fragrance claim is provided for this model.'),('Can it treat a skin condition?', 'No medical or treatment efficacy claim is available.')]),
'Roasted Almond Snack': (
 'Shelf-stable unopened roasted almond snack pack containing 200 g.',
 'Contains tree nuts; check the actual label for additional allergens or cross-contact disclosures.',
 'Store sealed and follow packaging instructions after opening.',
 'No certification of being allergen-free or a specific calorie/nutrition panel is provided.',
 [('Are there nuts in this snack?', 'Yes. The product is roasted almonds and contains tree nuts.'),('How large is the pack?', '200 grams.'),('Can someone with a tree-nut allergy eat it?', 'No; almonds are a tree-nut allergen.')]),
'Whole Grain Oats': (
 'Dry whole-grain oats in a 500 g pack for food preparation.',
 'Follow preparation instructions appropriate to the recipe and check any cross-contact allergen information.',
 'Keep sealed and dry; storage life after opening is not specified.',
 'Gluten-free certification and full nutrition facts are not supplied.',
 [('Are these certified gluten free?', 'No gluten-free certification is provided; check the label for cross-contact.'),('What is the pack weight?', '500 grams.'),('Can I eat these without cooking?', 'The information does not specify a ready-to-eat preparation claim; follow the package or recipe instructions.')]),
'Ground Coffee': (
 'Sealed 250 g pack of roasted ground coffee for brewing.',
 'Use an appropriate brewer and grind suitability; no grind-size specification or caffeine content per serving is given.',
 'Keep the opened bag sealed and away from moisture.',
 'This product contains caffeine; decaffeinated status is not claimed.',
 [('Is this decaffeinated?', 'No. It is described as containing caffeine.'),('Does it come as whole beans?', 'No. It is described as ground coffee.'),('Is the grind suitable for espresso?', 'The grind size is not specified; espresso suitability cannot be confirmed.')]),
'Dried Fruit Mix': (
 'Pack of assorted dried fruit weighing 200 g.',
 'Review the full package label for ingredients, sulfites and other allergens before recommending.',
 'Store sealed in a dry place according to packaging guidance.',
 'Exact fruit mix, sugar composition and nutritional information are not provided.',
 [('Does this contain sulfites?', 'The available information says to check the label for sulfites; their presence is not confirmed.'),('How much dried fruit is included?', '200 grams.'),('Is the mix sugar-free?', 'No added-sugar or total-sugar claim is documented.')]),
'Wooden Building Blocks': (
 '30-piece wooden block activity for children aged 3 years and older.',
 'Check the stated age suitability and supervise play; younger children may be at risk from small parts.',
 'Wipe the blocks and inspect for damage that could produce sharp edges or loose pieces.',
 'No specific safety certification, paint testing or suitability for children under three is documented.',
 [('How many blocks are included?', 'Thirty wooden blocks.'),('Can a two-year-old use this set?', 'The documented age is 3+ and there is a small-parts warning; do not recommend it for children under three.'),('Is adult supervision recommended?', 'Yes, especially for younger children.')]),
'Puzzle Set': (
 '120-piece cardboard puzzle activity marked for ages six and up.',
 'Choose for a child in the stated age range; pieces are not suitable for children under three.',
 'Keep pieces dry and store them together to avoid missing parts.',
 'Finished puzzle dimensions, exact artwork and independent safety certification are not specified.',
 [('How many pieces does it have?', 'One hundred and twenty.'),('Is this suitable for a toddler?', 'No. The stated age is 6+ and it is not suitable for children under three.'),('Is the puzzle made of wood?', 'No. The puzzle pieces are cardboard.')]),
'Remote Control Car': (
 'Toy remote-controlled car with a 2.4 GHz controller, marked for ages eight and up.',
 'Check the required battery types separately; batteries are not included and no charging system is specified.',
 'Use in an open play area and keep the controller dry.',
 'Range, battery endurance, speed and waterproofing are not specified.',
 [('Are batteries included?', 'No, batteries are explicitly not included.'),('What frequency does the controller use?', 'The controller uses 2.4 GHz.'),('Can it drive through water?', 'No water-protection rating is given; wet use is not recommended.')]),
'Art Activity Kit': (
 'Creative drawing activity containing crayons and paper, intended for ages five and up.',
 'Select by stated age and supervise children; exact color count and paper-sheet count are not given.',
 'Store crayons away from excessive heat and keep paper dry.',
 'Washability, non-toxicity certification and allergy suitability are not provided.',
 [('Does the kit contain paint?', 'Only crayons and paper are specified.'),('What age group is listed?', 'Ages 5+.'),('How many crayons are provided?', 'The exact crayon count is not included in the available description.')]),
'Training Yoga Mat': (
 'Indoor exercise foam mat 180 × 60 cm and 6 mm thick.',
 'Compare mat size and thickness with your exercise space and support preferences.',
 'Wipe clean and air dry before storage.',
 'No slip-resistance test, latex-free certification or outdoor weather durability is supplied.',
 [('How thick is the mat?', 'Six millimeters.'),('What are the dimensions?', '180 by 60 centimeters.'),('Is this yoga mat intended for outdoor sessions?', 'It is specified for indoor exercise; weather durability is not documented.')]),
'Insulated Sports Bottle': (
 'Reusable stainless-steel sports bottle with nominal capacity of 600 mL.',
 'Use for ordinary drinks; it is not designed for hot carbonated liquids.',
 'Hand wash; check the lid seal and dry fully before storage.',
 'No specific temperature-retention duration or dishwasher rating is supplied.',
 [('Can it hold 600 mL?', 'Its stated nominal volume is 600 milliliters.'),('Can I store hot carbonated drinks?', 'No. The compatibility note explicitly excludes hot carbonated liquids.'),('How long does it keep drinks cold?', 'No validated insulation-duration measurement is provided.')]),
'Resistance Band Set': (
 'Three-piece latex resistance-band set for controlled exercise.',
 'Choose exercises appropriate to strength and inspect bands for damage before use.',
 'Keep bands clean and avoid sharp objects or extreme stretch that could cause snapping.',
 'Contains latex; exact resistance ratings and exercise load ratings are not supplied.',
 [('Does this contain latex?', 'Yes. The material is listed as latex.'),('How many resistance bands are included?', 'Three.'),('What resistance level is each band?', 'Specific force/resistance levels are not documented.')]),
'Cycling Gloves': (
 'Padded-palm polyester-blend gloves for recreational cycling.',
 'Measure hand circumference for fit; the label does not specify numeric size conversions.',
 'Follow the garment care label and allow gloves to dry after use.',
 'No impact-protection certification, weatherproofing or touchscreen operation is specified.',
 [('How do I choose a size?', 'Use hand circumference and the product sizing chart, which is not provided here.'),('Do the gloves have padding?', 'Yes. A padded palm is specified.'),('Are they waterproof?', 'Waterproof construction is not documented.')]),
'Hex Key Set': (
 'Nine-piece steel metric hex key set covering nominal sizes 1.5 to 10 mm.',
 'Match the key exactly to the fastener hex size; these are metric keys, not imperial keys.',
 'Keep keys clean and dry after use and avoid excessive torque.',
 'No torque rating, electrical insulation rating or professional certification is supplied.',
 [('Are these imperial or metric?', 'Metric sizes from 1.5 to 10 mm are specified.'),('How many keys are in the set?', 'Nine.'),('Can these be used on live electrical equipment?', 'No electrical-insulation certification is listed.')]),
'Cordless Screwdriver': (
 'Compact 3.6 V lithium-battery screwdriver for ordinary household screwdriving.',
 'Use an appropriate bit and fastening task; do not interpret 3.6 V as a torque rating.',
 'Recharge through USB as specified and keep the tool dry.',
 'No drill capability, torque specification, water protection or professional duty-cycle rating is supplied.',
 [('Can it drill holes in masonry?', 'No. It is described only for household screwdriving.'),('How is it charged?', 'USB charging is specified.'),('What torque does it provide?', 'A torque rating is not included in the product description.')]),
'Tape Measure': (
 'Five-meter steel measuring tape marked in metric and imperial units.',
 'Choose the scale that matches the task and retract the blade with control.',
 'Wipe dry after use and avoid kinking the steel tape.',
 'No laboratory precision tolerance or certified calibration is stated.',
 [('Does it show inches?', 'Yes. Metric and imperial markings are specified.'),('What is the maximum tape length?', 'Five meters.'),('Can it be used for certified calibration?', 'No metrology or calibration certification is provided.')]),
'Utility Tool Organizer': (
 'Polyester storage case with multiple pockets for holding hand tools.',
 'Compare the actual tools with pocket sizes, which are not individually specified.',
 'Wipe the polyester case clean and dry before storing tools.',
 'Tools are not included; no maximum weight or waterproof rating is specified.',
 [('Are tools included?', 'No. The listing explicitly says tools are not included.'),('Is it made of leather?', 'No. Polyester is the stated material.'),('How much weight can it carry?', 'No certified load capacity is documented.')]),
'Car Phone Mount': (
 'Adjustable-grip dashboard phone holder using an adhesive mounting base.',
 'Check dashboard surface suitability and the phone dimensions before attaching.',
 'Clean and dry the mounting area following adhesive instructions; avoid applying to delicate surfaces.',
 'No specific phone-size range, heat-resistance rating or vehicle model list is given.',
 [('Will it fit every phone?', 'Not guaranteed. Grip dimensions and phone compatibility are not documented.'),('Can I attach it to a textured dashboard?', 'Surface suitability must be checked; adhesive compatibility is not guaranteed.'),('Is this a windshield suction mount?', 'No. It is described as a dashboard adhesive mount.')]),
'Interior Cleaning Cloths': (
 'Six reusable microfiber cloths for ordinary vehicle interior cleaning.',
 'Choose suitable cleaning methods for each vehicle surface; the cloths themselves do not include cleaning solution.',
 'Machine wash after use according to the product care label.',
 'No chemical resistance, electronics-safe or scratch-free certification is supplied.',
 [('How many cloths are in the pack?', 'Six.'),('Do the cloths include cleaner?', 'Only microfiber cloths are described; cleaning liquid is not listed.'),('Can they be machine-washed?', 'Yes. The care information says the cloths are machine washable.')]),
'Tire Pressure Gauge': (
 'Battery-powered digital gauge for Schrader tire valves with 0–100 psi range.',
 'Verify that the valve is Schrader and pressure is within range; confirm accuracy requirements separately.',
 'Keep the sensor clean and check the battery if the display does not turn on.',
 'No accuracy tolerance, other valve adaptor or calibration certification is supplied.',
 [('Can it measure above 100 psi?', 'No. The documented range is 0–100 psi.'),('Does it connect to Presta valves?', 'Only Schrader compatibility is stated.'),('What powers the display?', 'It is battery powered; exact battery size is not provided.')]),
'Emergency Flashlight': (
 'AA-battery-powered LED flashlight for general visibility.',
 'Use compatible AA batteries; they are not included in this product.',
 'Remove batteries before long storage and keep the contacts dry.',
 'Waterproofing, beam output, runtime and emergency certification are not documented.',
 [('Are AA batteries included?', 'No. Batteries are explicitly not included.'),('What kind of light source does it use?', 'An LED.'),('Is it waterproof for a storm?', 'No waterproof rating is specified.')]),
'Minimalist Pendant Necklace': (
 'Stainless-steel pendant necklace with an adjustable chain.',
 'Check the actual chain length and metal sensitivity; nickel content has not been verified.',
 'Wipe gently and avoid prolonged chemical exposure.',
 'Not described as nickel-free, hypoallergenic or precious-metal plated.',
 [('Is this nickel free?', 'Nickel content is not verified; do not claim nickel-free suitability.'),('Can the chain be adjusted?', 'Yes, an adjustable chain is specified.'),('Is it solid silver?', 'No. Stainless steel is the stated metal.')]),
'Classic Stud Earrings': (
 'Pair of stainless-steel stud earrings with secure backs.',
 'Check skin sensitivity and verify the backing style before purchase.',
 'Clean gently and inspect closures regularly.',
 'No nickel-free, medical-grade or hypoallergenic certification is supplied.',
 [('Is this a single earring?', 'No. A pair is described.'),('Are these safe for nickel allergies?', 'No nickel-content testing is supplied, so allergy suitability cannot be confirmed.'),('What material is listed?', 'Stainless steel.')]),
'Braided Bracelet': (
 'Adjustable braided accessory made with synthetic cord and a clasp.',
 'Use the adjustable closure for fit; numeric wrist size limits are not supplied.',
 'Keep the cord dry and allow it to air dry if it becomes damp.',
 'Not designed for water immersion; no precious-metal components or tensile rating documented.',
 [('Can I swim while wearing this?', 'No. It is not designed for water immersion.'),('Can the clasp be adjusted?', 'Yes. The closure is described as adjustable.'),('Is the cord leather?', 'No. Synthetic cord is specified.')]),
'Everyday Ring': (
 'Stainless-steel ring sold in assorted sizes.',
 'Measure ring size using a sizing guide before ordering; precise sizes are not listed here.',
 'Wipe clean and limit exposure to harsh chemicals.',
 'No nickel-free guarantee or sizing exchange policy is supplied.',
 [('How do I choose the ring size?', 'Use a ring-size guide and verify the actual available size; numeric size inventory is not given.'),('Is the ring stainless steel?', 'Yes, stainless steel is specified.'),('Is it suitable for nickel sensitivity?', 'Nickel content is not documented; sensitivity suitability cannot be confirmed.')]),
'Reusable Shopping Tote': (
 'Cotton-canvas reusable tote with approximate capacity of 15 liters.',
 'Use for ordinary shopping items while respecting unspecified weight limits.',
 'Allow the fabric to dry before storing; detailed wash temperature is not given.',
 'No rated maximum load, insulated lining or waterproof construction is documented.',
 [('How much can it hold?', 'Approximately 15 liters by volume; no safe weight capacity is provided.'),('Can I use it for frozen groceries?', 'No insulation or temperature-control capability is listed.'),('Is it made from plastic?', 'No. Cotton canvas is specified.')]),
'Travel Cable Pouch': (
 'Polyester zipped pouch with three mesh pockets for organizing travel accessories.',
 'Check actual device and charger dimensions against the pouch; pocket measurements are not specified.',
 'Wipe clean and dry after travel.',
 'Accessories are not included and no waterproof or drop-test rating is documented.',
 [('How many mesh pockets are there?', 'Three.'),('Does it include USB cables?', 'No. Accessories are not included.'),('Is the pouch waterproof?', 'No waterproof protection is specified.')]),
'Desk Notebook': (
 'A5-size paper notebook with 120 ruled pages.',
 'Use it for handwriting; no digital synchronization or app is included.',
 'Keep the pages dry and avoid bending the binding.',
 'No paper-weight grade, refill format or archival certification is supplied.',
 [('How many pages does it have?', '120 ruled pages.'),('Can it sync notes to a phone?', 'No. It has no digital synchronization feature.'),('What page size is specified?', 'A5.')]),
'Reusable Gift Bag': (
 'Medium paperboard gift bag with rope handles.',
 'Choose based on gift dimensions and unknown maximum load; do not assume it supports heavy objects.',
 'Keep the paperboard dry and avoid overloading handles.',
 'No certified weight rating or waterproofing is provided.',
 [('Is the bag waterproof?', 'No. Paperboard construction is not specified as water resistant.'),('What kind of handles does it have?', 'Rope handles.'),('Can it carry a heavy appliance?', 'No load capacity is provided, so heavy-use suitability cannot be confirmed.')]),
}

VIETNAMESE_TERMS = {
'electronics': 'thiết bị điện tử, phụ kiện máy tính, tai nghe, loa, sạc USB-C',
'apparel': 'quần áo, áo phông, áo khoác, quần chinos',
'books': 'sách giấy, sách hướng dẫn, sách tiếng Anh',
'home_goods': 'đồ gia dụng, cốc, chăn, đèn bàn, hộp đựng',
'beauty': 'chăm sóc cá nhân, sữa rửa mặt, kem dưỡng, dưỡng tóc',
'food': 'thực phẩm, hạt, yến mạch, cà phê, trái cây khô',
'toys': 'đồ chơi, lắp ghép, ghép hình, xe điều khiển',
'sports': 'thể thao, yoga, bình nước, dây kháng lực, găng tay',
'tools': 'dụng cụ, chìa lục giác, máy vặn vít, thước dây',
'automotive': 'phụ kiện ô tô, giá đỡ điện thoại, đồng hồ áp suất lốp',
'jewelry': 'trang sức, vòng cổ, bông tai, vòng tay, nhẫn',
'other': 'phụ kiện, túi mua sắm, túi dây cáp, sổ tay, túi quà',
}




SHOPPING_AND_SUPPORT = {'Wireless Earbuds': 'Before choosing these earbuds for calls, confirm that the phone or computer can use Bluetooth audio and select a suitable microphone profile. When one bud fails to connect, charge both buds, check pairing availability, and reconnect from the host device. The charging cable is not an alternative audio connection.', 'Portable Speaker': 'Use this speaker where Bluetooth playback is sufficient; the product description does not include a cable-input option. For use at a desk or in a room, consider where it can be charged without moisture exposure. The 10-hour figure is a rating, so do not plan an event around guaranteed playback at maximum volume.', 'USB-C Hub': 'When recommending this hub for an external monitor, ask whether the computer supports video over its USB-C port. A USB-C connector that carries data only cannot drive the HDMI output. Confirm the monitor input and cable before troubleshooting. The 60 W figure describes the hub’s passthrough rating; it is not a promise that every laptop will charge.', 'Laptop Sleeve': 'The 13-inch label refers to a general laptop size class, not a universal fit. Customers should compare the laptop’s external width, depth and thickness, especially if a protective shell is fitted. A padded sleeve helps reduce routine scratches during transport but is not a substitute for a hard case in a drop.', 'Wireless Charging Pad': 'This pad is intended for phones and accessories with Qi receiving capability. A USB-C input alone does not mean a phone supports wireless charging. Position the device centrally; thick cases and metal objects can interfere with charging. Customers must supply a suitable power adapter, because one is not included.', 'Everyday Cotton T-Shirt': 'This is a basic regular-fit shirt intended for everyday wear rather than technical sports protection. Choose by garment measurements instead of assuming that a familiar letter size is identical across brands. Since shrinkage and finished garment measurements are not listed here, avoid promising a precise post-wash fit.', 'Lightweight Hoodie': 'A lightweight hoodie works as a casual extra layer, but its insulation level is not measured. For wearing over a T-shirt, compare chest and length dimensions with the expected layering fit. The unspecified cotton-blend percentages should not be represented as a particular composition or guaranteed thermal performance.', 'Travel Jacket': 'Choose this jacket for an additional wind-resistant outer layer, not as a raincoat. If a customer needs dependable rain protection, look for a model with an explicit waterproof rating and construction details. Check outerwear sizing with any layers the customer plans to wear underneath.', 'Relaxed Fit Chinos': 'Relaxed-fit chinos should be selected using both waist and inseam measurements. The described fabric is cotton twill, and the care instruction is cold machine washing. A relaxed cut is not a substitute for correct size; no stretch percentage or tailored length is given.', 'Everyday Polo Shirt': 'The short-sleeve cotton-knit construction is suited to ordinary casual wear. Before purchase, check the garment chart for collar, chest and length rather than relying only on a size label. Detailed shrinkage, fabric weight and performance treatments are not specified.', 'Practical Photography Handbook': 'This paperback is suitable for readers looking for an illustrated introductory reference. The physical book is what is included; the listing does not contain access to an online course, an e-book license or downloadable exercises. Check that the customer wants an English-language print book.', 'Everyday Cooking Guide': 'The guide provides illustrated recipes in a paperback format. Customers with dietary restrictions should review individual recipe ingredients rather than assuming the book is allergen-free or tailored to a specific diet. Purchase includes the printed English-language book only.', 'Introduction to Data Analysis': 'This printed introduction is designed around worked examples and explanations. It is not bundled with a software license, online classroom or automatic updates. Buyers who need a particular programming language or statistical package should confirm coverage before choosing it.', 'Urban Gardening Guide': 'The photography and explanations are useful as a general home-gardening reference. Local temperatures, growing seasons and planting restrictions vary, so examples may need adjustment to the reader’s region. This paperback is not a substitute for local agricultural or regulatory guidance.', 'Ceramic Coffee Mug': 'The mug has a nominal capacity of 350 mL. Because microwave and dishwasher certification are not supplied, hand washing is the stated care option. Buyers should not interpret ceramic construction alone as confirmation that the mug is suitable for heating in a microwave.', 'Cotton Throw Blanket': 'At 130 by 170 centimeters, this throw is intended for use as a home textile. Compare these dimensions with a sofa, chair or bed before purchase. The cold-wash care instruction should be followed; the information does not establish thermal insulation or outdoor-weather performance.', 'LED Desk Lamp': 'This lamp requires a compatible 5 V USB power supply. A 5 W nominal specification describes electrical consumption, not a guaranteed brightness or desk illumination level. Customers needing dimming, color-temperature settings or a supplied wall plug should verify those features separately.', 'Kitchen Storage Set': 'The set contains three BPA-free plastic containers for ordinary storage. Buyers should check whether the available capacity and container shapes suit their planned ingredients, because exact volumes are not listed. The containers are hand-wash items and are not presented as oven-safe.', 'Gentle Face Cleanser': 'This fragrance-free cleanser is intended for external facial cleansing, not as a treatment for a specific skin condition. A user with reactive skin may test a small area according to the product label. A complete ingredient list is not supplied in this summary, so customers with known sensitivities should check the package.', 'Daily Moisturizer': 'This is a 50 mL glycerin-based moisturizer for ordinary skin care. Skin reactions vary and the description does not promise a medical benefit. Customers looking for sunscreen protection should choose a separately rated SPF product; no SPF rating is supplied here.', 'Hair Conditioning Mask': 'Use this rinse-out conditioning product according to the packaging instructions after washing the hair. It is not identified as a leave-in treatment. Customers with color-treated or sensitive hair should review the complete ingredient information before relying on a compatibility claim.', 'Hand Cream': 'The 75 mL tube is intended for daily hand moisturizing. It is not described as a medicated treatment and should not be recommended for treating damaged or infected skin. Customers concerned about fragrance or allergies need the full ingredient declaration, which is not included here.', 'Roasted Almond Snack': 'Almonds are tree nuts and an allergen, so this snack is unsuitable for a customer with a tree-nut allergy. The packet contains 200 g. Information on other allergens, cross-contact and nutritional values should be checked on the physical label rather than inferred from the product name.', 'Whole Grain Oats': 'This 500 g pack contains dry whole-grain oats for preparing food. Whether a recipe needs cooking, soaking or another method depends on its instructions. The listing does not claim gluten-free certification; customers avoiding gluten need to check the packaging for sourcing and cross-contact details.', 'Ground Coffee': 'This is a 250 g pack of ground coffee, not whole beans. Because the grind size is not specified, it cannot be assumed suitable for a particular espresso machine or brewing method. Keep the opened pack sealed to reduce moisture exposure and preserve everyday freshness.', 'Dried Fruit Mix': 'The pack contains 200 g of assorted dried fruit. Customers managing sugar intake or sulfite sensitivity should consult the ingredient and nutrition label. The summary does not specify the mix of fruits or declare that the product contains no added sugar.', 'Wooden Building Blocks': 'The set contains 30 wooden blocks for ages three and older. It is not an appropriate choice for a child below the stated age because of small-parts concerns. Adults should inspect pieces for damage and supervise play rather than assuming a safety test not listed for this set.', 'Puzzle Set': 'This 120-piece cardboard puzzle is labeled for children aged six and up. It works best for a child interested in a multi-piece assembly activity rather than a very young toddler. The listing does not establish completed dimensions, so frame or table sizing cannot be confirmed.', 'Remote Control Car': 'The car is controlled on the 2.4 GHz band and intended for ages eight and above. Batteries are not included; confirm battery type before giving it as a gift. The toy is not specified for wet surfaces, and its range or run time is not listed.', 'Art Activity Kit': 'The kit includes crayons and paper for creative activity from age five. The description does not include paint or markers, so purchasers should not expect those materials. A parent or caregiver should supervise use; the exact number of crayons and sheets is not given.', 'Training Yoga Mat': 'The mat measures 180 by 60 centimeters and is 6 millimeters thick. Compare those dimensions with the user’s height, exercise area and preference for cushioning. It is described for indoor exercise; an outdoor-weather rating and independent slip-resistance test are not supplied.', 'Insulated Sports Bottle': 'The 600 mL nominal volume is suitable for everyday beverages. A hand-wash routine is specified, and the bottle should be dried with the lid open after cleaning. Avoid hot carbonated liquids because that use is explicitly excluded. No hold-time guarantee for hot or cold drinks is listed.', 'Resistance Band Set': 'The set contains three latex bands. Because the exact resistance levels are not provided, do not choose it solely for a target load or rehabilitation program requiring measured tension. Inspect bands before stretching, and avoid use where a latex allergy is a concern.', 'Cycling Gloves': 'These gloves use a padded palm and polyester-blend fabric for recreational riding. Fit should be determined by hand circumference rather than an assumed clothing size. There is no stated impact certification, touchscreen feature or waterproof barrier, so they should not be sold as specialist protective equipment.', 'Hex Key Set': 'The nine-piece set covers metric hex sizes from 1.5 to 10 mm. Match the fastener exactly before applying force, since imperial hex fittings require different sizes. These keys are not rated as insulated electrical tools or certified torque-measuring instruments.', 'Cordless Screwdriver': 'The compact 3.6 V screwdriver is intended for ordinary household screws. It should be paired with an appropriate bit and is not described as a masonry drill. Voltage is not a measure of output torque. The product uses USB charging, but detailed charging time and torque settings are not supplied.', 'Tape Measure': 'The five-meter steel tape carries both metric and imperial markings. Choose a consistent measurement scale for a project and retract the blade carefully. The listing describes general measuring use, not a certified calibration instrument with a published tolerance.', 'Utility Tool Organizer': 'This polyester organizer has multiple pockets for storing hand tools. The case does not include tools. Customers should compare pocket dimensions with their own tools, as pocket sizing and safe carrying weight are not specified. It is a storage accessory, not an impact-rated protective case.', 'Car Phone Mount': 'The adjustable dashboard mount needs a suitable clean mounting surface. Its adhesive fit is not guaranteed for every dashboard finish or texture. Before driving, confirm that the installed mount holds the device securely without obstructing visibility or vehicle controls.', 'Interior Cleaning Cloths': 'The pack contains six reusable microfiber cloths for vehicle interior maintenance. No detergent or cleaning chemical is included. Follow the care instructions when washing; delicate vehicle surfaces may have their own treatment requirements, which should be checked before using a cloth with cleaning products.', 'Tire Pressure Gauge': 'This digital gauge is designed for Schrader valves and reads pressures up to 100 psi. Verify the valve type on the vehicle or accessory before purchase. Accuracy tolerance and calibration certification are not given, so it should not be represented as a precision service instrument.', 'Emergency Flashlight': 'The flashlight uses an LED and AA batteries, which are not included. Keep replacement batteries available if it is stored for occasional use. No waterproof rating, output rating or guaranteed run time is given, so do not rely on it as certified emergency equipment.', 'Minimalist Pendant Necklace': 'This pendant necklace uses stainless steel and an adjustable chain. Buyers should check the actual chain length and personal metal sensitivities. Since nickel content and hypoallergenic certification are not provided, it is not appropriate to promise suitability for a nickel allergy.', 'Classic Stud Earrings': 'The package contains a pair of stainless-steel stud earrings. Confirm the closure style and the wearer’s metal tolerance before purchase. No nickel-free or medical-grade certification is given. Routine cleaning and checks on the backing help with ordinary wear.', 'Braided Bracelet': 'The adjustable synthetic-cord bracelet is intended as a casual accessory. It is not described as leather and is not designed to be immersed in water. Customers who need exact wrist-size limits should verify measurements because the adjustment range is not specified.', 'Everyday Ring': 'This stainless-steel ring is offered in assorted sizes. A customer should check ring size before ordering rather than inferring fit from another brand. Nickel content is not provided, and the product description does not establish a special sizing exchange entitlement.', 'Reusable Shopping Tote': 'The cotton-canvas tote has about 15 liters of volume. That figure does not state the maximum safe carrying weight. It works as an ordinary shopping bag but is not an insulated food carrier or a waterproof bag. Keep fabric dry before long-term storage.', 'Travel Cable Pouch': 'This polyester pouch includes three mesh pockets for cables and travel accessories. A phone charger or USB cable is not included. The precise pocket dimensions are not given, so oversized adapters should be checked for fit. The case has no stated waterproof or drop rating.', 'Desk Notebook': 'This A5 notebook contains 120 ruled pages. It is suitable for handwritten notes and does not connect to a phone or cloud application. Customers needing archival-quality paper, a removable refill or a particular paper weight should confirm those features separately.', 'Reusable Gift Bag': 'The medium paperboard bag has rope handles and is intended for ordinary gifts. The information does not provide an approved load rating, so heavy appliances are not a suitable recommendation without more detail. Keep paperboard away from moisture and avoid overloading the handles.'}



DEEP_DIVE = {'USB-C Hub': ('Connection checklist', 'Connect the hub directly to the host USB-C port. For external display use, the host port must support video output, such as DisplayPort Alternate Mode; a data-only USB-C port will not send a picture. Start troubleshooting with a single monitor and a known-working HDMI cable, then confirm the correct monitor input. The four USB ports are expansion connections, not replacements for the computer’s host port.', 'Charging and desk setup', 'The 60 W figure is the stated maximum power passthrough of the hub. It is not a guarantee that the connected laptop will receive 60 W after the hub’s own consumption or that every USB-C adapter is suitable. Confirm the power adapter and laptop requirements before promising a charging outcome.', 'Support example', 'If a keyboard connected through the hub works but HDMI does not, the likely next check is the host’s video-output capability, rather than assuming the entire hub is faulty.'), 'Wireless Earbuds': ('Pairing and audio profiles', 'First charge the earbuds and open Bluetooth discovery on the phone or computer. Select the earbuds as the output device; for calls, also check the microphone input selection. USB-C is used for charging, not as a direct wired audio connection.', 'Fit and battery care', 'Keep charging contacts dry and clean; put the earbuds in the charging case between sessions. Battery endurance varies with playback volume and call use. A Bluetooth version number alone does not establish multipoint connectivity or noise cancellation.', 'Support example', 'If music plays but a meeting app uses the laptop microphone, change the audio input device inside the meeting app. That is an audio-routing check, not necessarily a Bluetooth pairing failure.'), 'Wireless Charging Pad': ('Device and power compatibility', 'Look for Qi receiving capability in the phone or accessory. A USB-C charge port on a phone does not itself establish Qi support. The pad needs its own suitable USB-C power adapter, which is not included.', 'Placement checks', 'Place the receiving coil close to the middle of the charging surface; move thick or metallic cases out of the path if the device does not start charging. Remove loose metal objects from the pad.', 'Support example', 'If the charging indicator switches on but the phone does not charge, confirm Qi support, remove the case, reseat the phone and check the external power adapter before assuming a hardware fault.'), 'Laptop Sleeve': ('Fit verification', 'The 13-inch description is a laptop size class rather than a full internal-dimension guarantee. Measure the laptop’s width, depth and thickness, including any fitted protective shell, before selecting a sleeve.', 'Protection level', 'The padded compartment helps with ordinary scratches and minor movement inside a bag. It is not a certified drop-protection enclosure. Keep liquids and sharp objects away from the sleeve.', 'Support example', 'Two laptops with 13-inch screens can have different body footprints. A customer whose laptop has thick bezels should check exterior dimensions, not just screen size.'), 'Portable Speaker': ('Audio source setup', 'Use a Bluetooth-capable playback source and select the speaker as the active audio output. Check volume on both the phone and speaker. The available description does not establish a 3.5 mm audio input or microphone function.', 'Playback planning', 'Ten hours is a rated playback figure, not a guarantee at maximum volume. For long events, plan convenient USB-C charging and do not assume water resistance unless a rating is shown.', 'Support example', 'If the speaker pairs successfully but remains silent, check whether the source device is sending its output to another device and then verify both volume settings.'), 'LED Desk Lamp': ('Power and placement', 'The desk lamp is specified for 5 V USB power with a nominal consumption of 5 W. A computer USB port or external adapter must deliver compatible power. Position the lamp so it illuminates the work area without directing glare into the eyes.', 'Choosing by task', 'A 5 W electrical input does not establish luminous flux, color temperature or dimming capability. Customers with specialized drafting or reading requirements should look for measured brightness and adjustability specifications.', 'Support example', 'If the lamp does not turn on, first verify the USB supply and cable connection. Do not interpret a wattage rating as a statement of compatibility with mains electricity.'), 'Gentle Face Cleanser': ('Routine placement', 'Use this 200 mL fragrance-free cleanser as a wash-off step and rinse with water. Follow with suitable moisturizer. Fragrance-free does not mean that every customer will tolerate every ingredient.', 'Sensitivity considerations', 'A patch test can help identify personal irritation, but it is not a substitute for a complete ingredient declaration or medical advice. Stop use if irritation appears. Keep product out of the eyes.', 'Support example', 'If a customer reports stinging, ask them to discontinue use and check the package ingredient list rather than claiming that the cleanser is universally hypoallergenic.'), 'Whole Grain Oats': ('Preparation and portions', 'The 500 g package contains dry oats intended for cooking or recipe use. Customers should check their own preparation instructions and portion sizes; the listing does not certify an instant or ready-to-eat preparation method.', 'Storage and dietary checks', 'Keep the pack sealed and dry after opening. Customers with gluten-related dietary restrictions need a suitable packaging declaration because the listing does not provide a gluten-free certification.', 'Support example', 'For a customer asking whether the oats are safe for a gluten-free diet, direct them to actual allergen and cross-contact labeling, not just the word “oats” in the name.'), 'Cordless Screwdriver': ('Supported work', 'This 3.6 V rechargeable tool is intended for ordinary household screwdriving with an appropriate bit. It is not described as a drill for masonry or a high-torque impact driver.', 'Charging and bit selection', 'Charge through the specified USB connection and keep the tool dry. Use the correct bit profile and size so that the screw head is not damaged. Voltage should not be treated as torque output.', 'Support example', 'If the driver spins but a screw does not tighten, confirm the bit fits the screw and consider whether the material needs pilot-hole preparation. The documented product has no rated drilling function.'), 'Tire Pressure Gauge': ('Measurement procedure', 'Use the digital gauge on compatible Schrader valves; align the gauge squarely with the valve stem to minimize air leakage. Read and compare the pressure to the vehicle manufacturer’s specification, which is usually given on the vehicle placard.', 'Range and limits', 'The instrument measures within its stated 0–100 psi range. That range does not establish a calibration certificate, accuracy tolerance or compatibility with other valve types.', 'Support example', 'If a reading seems unusually low after disconnecting the gauge, check the tire for leakage and repeat the measurement with a secure seal. Never substitute a generic target pressure for the vehicle placard.')}

def render(p: dict, name: str, spec: str, compat: str, *, variant: int = 1) -> str:
    """Render a customer-support-ready product guide, without pipeline instructions.

    The stable product key and generation provenance live in product_enrichment,
    knowledge_documents and the release manifest rather than in the guide body.
    """
    if name not in DETAILS:
        raise KeyError(f'Missing product details for {name}')
    if variant != 1:
        raise ValueError('Variant alias without variant-specific facts is not allowed')
    overview, selection, care, limitations, questions = DETAILS[name]
    if len(questions) != 3:
        raise ValueError(f'Expected three product-specific FAQ for {name}')

    category = p['category']
    specifications_heading = {
        'apparel': 'Fabric and fit', 'books': 'Edition and format',
        'food': 'Pack information and ingredients', 'beauty': 'Formula and packaging',
        'jewelry': 'Materials and sizing', 'toys': 'Contents and age guidance',
        'sports': 'Materials and dimensions', 'electronics': 'Features and connections',
        'home_goods': 'Materials and specifications', 'automotive': 'Fit and specifications',
        'tools': 'Tool specifications', 'other': 'Materials and features',
    }[category]
    selection_heading = {
        'apparel': 'Choosing the right fit', 'books': 'Who this book is for',
        'food': 'Before serving', 'beauty': 'Choosing and applying the product',
        'jewelry': 'Fit and skin considerations', 'toys': 'Age and use guidance',
        'sports': 'Choosing and using the product', 'electronics': 'Compatibility and setup',
        'home_goods': 'Placement and everyday use', 'automotive': 'Vehicle and use compatibility',
        'tools': 'Selecting and using the tool', 'other': 'Choosing the product',
    }[category]
    care_heading = 'Care and maintenance' if category not in ('food', 'books') else ('Storage' if category == 'food' else 'Keeping the book in good condition')
    faq = ''.join(f'### {q}\n{a}\n\n' for q, a in questions)
    deeper = DEEP_DIVE.get(name)
    deep_text = ''
    if deeper:
        headings, paragraphs = deeper[::2], deeper[1::2]
        deep_text = ''.join(f'## {h}\n{v}\n\n' for h,v in zip(headings, paragraphs))
    # No source IDs, raw import labels, test terminology or instructions to AI here.
    return (f'# {name}\n\n'
            f'## Overview\n{overview}\n\n'
            f'## {specifications_heading}\n{spec}.\n\n'
            f'## {selection_heading}\n{compat}. {selection}\n\n'
            f'## {care_heading}\n{care}\n\n'
            f'## Shopping and support notes\n{SHOPPING_AND_SUPPORT[name]}\n\n'
            f'{deep_text}'
            f'## Additional product information\n{limitations}\n\n'
            f'## Frequently asked questions\n{faq}')
