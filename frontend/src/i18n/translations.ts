export const translations = {
  en: {
    filters: 'Filters',
    satelliteLayers: 'Satellite Layers',
    selectArea: 'Select Area',
    language: 'Language',
    darkMode: 'Dark Mode',
    lightMode: 'Light Mode',
    about: 'About',
    aboutTitle: 'About SattelishMaps',
    aboutDescription: 'Satellite imagery analysis platform for Slovakia. Visualize NDVI, NDWI, NDBI, and Moisture indices using Sentinel-2 data.',
    close: 'Close',
    searchLocation: 'Search location...',
    areaAnalysis: 'Area Analysis',
    from: 'From',
    to: 'To',
    aiAnalysis: 'AI Analysis',
    export: 'Export',
    saveChart: 'Save Chart',
    saveReport: 'Save Report',
    drawHint: 'Hold Shift and drag to select area',
    layers: {
      ndvi: 'NDVI',
      ndwi: 'NDWI',
      ndbi: 'NDBI',
      moisture: 'Moisture'
    }
  },
  sk: {
    filters: 'Filtre',
    satelliteLayers: 'Satelitné vrstvy',
    selectArea: 'Vybrať oblasť',
    language: 'Jazyk',
    darkMode: 'Tmavý režim',
    lightMode: 'Svetlý režim',
    about: 'O aplikácii',
    aboutTitle: 'O SattelishMaps',
    aboutDescription: 'Platforma na analýzu satelitných snímok pre Slovensko. Vizualizujte NDVI, NDWI, NDBI a vlhkostné indexy pomocou údajov Sentinel-2.',
    close: 'Zavrieť',
    searchLocation: 'Hľadať lokalitu...',
    areaAnalysis: 'Analýza oblasti',
    from: 'Od',
    to: 'Do',
    aiAnalysis: 'AI Analýza',
    export: 'Export',
    saveChart: 'Uložiť graf',
    saveReport: 'Uložiť správu',
    drawHint: 'Podržte Shift a ťahajte pre výber oblasti',
    layers: {
      ndvi: 'NDVI',
      ndwi: 'NDWI',
      ndbi: 'NDBI',
      moisture: 'Vlhkosť'
    }
  }
};

export type Language = keyof typeof translations;
export type TranslationKey = keyof typeof translations.en;
