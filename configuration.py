import configparser


class Configuration:
    def __init__(self):
        self._config_file = self._create() 

    def _create(self):
        nome_file = 'impostazioni.ini'
        config = configparser.ConfigParser()
        config.read(nome_file)

        if len(config.sections()) == 0:
            config['generali'] = {
                'debug_mode': 'false',
                'cf_amministrazione': '00124430323',
                'ignora_colonne': 'COD_CPV,DESCRIZIONE_CPV,FLAG_PREVALENTE'
            }
            config['cartelle'] = {
                'cartella_cig': 'cig',
                'altre_cartelle': 'cup, aggiudicatari'
            }
            with open(nome_file, 'w') as configfile:
                config.write(configfile)
            
        return config
    
    def get_cig_folder(self) -> str:
        return self._config_file.get('cartelle', 'cartella_cig', fallback='cig')
    
    def get_other_folders(self) -> list[str]:
        return self._get_list_from_value(self._config_file.get('cartelle', 'altre_cartelle', fallback=''), False)
    
    def get_debug_mode(self) -> bool:
        return self._config_file.getboolean('generali', 'debug_mode', fallback=False)
        
    def get_columns_to_ignore(self) -> list[str]:
        return self._get_list_from_value(self._config_file.get('generali', 'ignora_colonne', fallback=''), True)
        
    def get_cf_amministrazione(self) -> str:
        return self._config_file.get('generali', 'cf_amministrazione', fallback='00124430323')
    
    def _get_list_from_value(self, value, to_upper: bool) -> list[str]:
        my_list = []
        if value != '':
            for x in value.split(','):
                x = x.strip()
                if to_upper:
                    x = x.upper()
                my_list.append(x)
        
        return my_list
    