[out:json][timeout:900];
area["ISO3166-2"="RU-TY"]->.ty;
(
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|track|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|living_street|road)$"](area.ty);
  way["route"="ferry"](area.ty);
);
out tags geom;
