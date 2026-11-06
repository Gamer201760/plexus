[out:json][timeout:600];
// коридор Тыва → Абакан/Минусинск (Хакасия, юг Красноярского края): только основные дороги
way["highway"~"^(motorway|trunk|primary|secondary|tertiary|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"](51.4,89.5,54.0,94.0);
out tags geom;
