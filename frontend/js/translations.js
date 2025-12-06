const translations = {
    sk: {
        // Sidebar
        "menu.map": "Mapa",
        "menu.search": "Hľadať",
        "menu.filters": "Filtre",
        "menu.stats": "Štatistiky",
        "menu.layers": "Vrstvy",
        "menu.theme": "Téma",
        "menu.language": "SK",
        "menu.info": "Info",

        // Filters
        "filters.title": "Filtre",
        "filters.layers": "Satelitná vrstva",
        "filters.ndvi": "NDVI",
        "filters.ndwi": "NDWI",
        "filters.ndbi": "NDBI",
        "filters.moisture": "Moisture",
        "filters.select_area": "Nová oblasť",
        "filters.placeholder": "Miesto pre budúce filtre...",

        // Stats Panel
        "stats.title": "Analýza oblasti",
        "stats.date_from": "Od:",
        "stats.date_to": "Do:",
        "stats.ai_title": "AI Analýza",
        "stats.loading_analysis": "Načítavam analýzu...",
        "stats.export_btn": "Stiahnuť",
        "stats.export_text": "Stiahnuť text",
        "stats.export_chart": "Stiahnuť graf",

        // Chart
        "chart.ndvi": "NDVI (Vegetácia)",
        "chart.ndwi": "NDWI (Voda)",
        "chart.ndbi": "NDBI (Zástavba)",
        "chart.moisture": "Moisture",
        "chart.months": ['Jan', 'Feb', 'Mar', 'Apr', 'Máj', 'Jún', 'Júl', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'],

        // AI Analysis Texts
        "ai.ndvi_only": "Zaznamenaný stabilný rast vegetačného indexu v jarných mesiacoch, čo indikuje zdravý vývoj plodín v tejto oblasti. Maximálne hodnoty dosahuje v júni, následne dochádza k prirodzenému poklesu spojenému s dozrievaním alebo sezónnymi zmenami.",
        "ai.ndwi_only": "Index NDWI vykazuje stabilné hodnoty vodného režimu. Mierne výkyvy v letných mesiacoch môžu naznačovať sezónne vysychanie povrchových vôd, avšak celkový trend zostáva v normále pre danú oblasť.",
        "ai.ndbi_only": "Index NDBI ukazuje mieru zastavania územia. Vyššie hodnoty indikujú hustú zástavbu alebo spevnené plochy, zatiaľ čo nižšie hodnoty zodpovedajú prírodným plochám.",
        "ai.moisture_only": "Index vlhkosti (Moisture) sleduje obsah vody v vegetácii a pôde. Pokles hodnôt môže signalizovať vodný stres alebo sucho v sledovanom období.",
        "ai.comparison": "Porovnanie NDVI a NDWI ukazuje silnú koreláciu medzi dostupnosťou vlahy a rastom vegetácie. Pokles vodného indexu (NDWI) v júli predchádza miernemu zníženiu vitality vegetácie (NDVI) v auguste, čo potvrdzuje závislosť na zrážkach.",
        "ai.no_data": "Žiadne dáta na zobrazenie. Vyberte vrstvy pre analýzu."
    },
    en: {
        // Sidebar
        "menu.map": "Map",
        "menu.search": "Search",
        "menu.filters": "Filters",
        "menu.stats": "Statistics",
        "menu.layers": "Layers",
        "menu.theme": "Theme",
        "menu.language": "EN",
        "menu.info": "Info",

        // Filters
        "filters.title": "Filters",
        "filters.layers": "Satellite Layer",
        "filters.ndvi": "NDVI",
        "filters.ndwi": "NDWI",
        "filters.ndbi": "NDBI",
        "filters.moisture": "Moisture",
        "filters.select_area": "New Area",
        "filters.placeholder": "More filters coming soon...",

        // Stats Panel
        "stats.title": "Area Analysis",
        "stats.date_from": "From:",
        "stats.date_to": "To:",
        "stats.ai_title": "AI Analysis",
        "stats.loading_analysis": "Loading analysis...",
        "stats.export_btn": "Download",
        "stats.export_text": "Download Text",
        "stats.export_chart": "Download Chart",

        // Chart
        "chart.ndvi": "NDVI (Vegetation)",
        "chart.ndwi": "NDWI (Water)",
        "chart.ndbi": "NDBI (Built-up)",
        "chart.moisture": "Moisture",
        "chart.months": ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],

        // AI Analysis Texts
        "ai.ndvi_only": "Stable growth of the vegetation index recorded in spring months, indicating healthy crop development in this area. Maximum values are reached in June, followed by a natural decline associated with maturation or seasonal changes.",
        "ai.ndwi_only": "The NDWI index shows stable water regime values. Slight fluctuations in summer months may indicate seasonal drying of surface waters, but the overall trend remains normal for the area.",
        "ai.ndbi_only": "The NDBI index indicates the density of built-up areas. Higher values suggest dense urban development or paved surfaces, while lower values correspond to natural areas.",
        "ai.moisture_only": "The Moisture Index tracks water content in vegetation and soil. A decline in values may signal water stress or drought during the observed period.",
        "ai.comparison": "Comparison of NDVI and NDWI shows a strong correlation between moisture availability and vegetation growth. The decline in the water index (NDWI) in July precedes a slight decrease in vegetation vitality (NDVI) in August, confirming dependence on precipitation.",
        "ai.no_data": "No data to display. Select layers for analysis."
    }
};
