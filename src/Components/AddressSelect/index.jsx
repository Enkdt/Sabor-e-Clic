import './AddressSelect.css'
import { useState } from 'react';

import {
    CountrySelect,
    StateSelect,
    CitySelect
} from 'react-country-state-city';

export const AddressSelect = () => {
    const [country, setCountry] = useState(null);
    const [state, setState] = useState(null);
    const [city, setCity] = useState(null);

    const handleCountryChange = (selectedCountry) => {
        setCountry(selectedCountry);
        setState(null);
        setCity(null);
    };

    const handleStateChange = (selectedState) => {
        setState(selectedState);
        setCity(null);
    };

    return (
        <div className="addressSelect">

            <div className="addressField">
                <label>País</label>

                <CountrySelect
                    onChange={handleCountryChange}
                    placeHolder="Selecione seu país"
                />
            </div>

            <div className="addressField">
                <label>Estado</label>

                <StateSelect
                    countryid={country?.id}
                    onChange={handleStateChange}
                    defaultValue={state}
                    placeHolder="Selecione seu estado"
                />
            </div>

            <div className="addressField">
                <label>Cidade</label>

                <CitySelect
                    countryid={country?.id}
                    stateid={state?.id}
                    onChange={setCity}
                    defaultValue={city}
                    placeHolder="Selecione sua cidade"
                />
            </div>

        </div>
    );
};
