import { Banner } from '../Assets/Banner'
import { BancadaImg } from '../Assets/BancadaImg'
import { Calendario } from './Calendario'
import { NextBtn } from '../Components/NextBtn'
import { NavLink } from 'react-router-dom'
import './Bancada.css'
export const Bancada=()=>{
    return (
        <>
            <Banner/>
            <div>
                <BancadaImg/>
                <div>
                    {/* Fazer tudo isso mudar dinamicamente também */}
                    <h1>República I</h1>
                    Rua Augusta - 120 - República - São Paulo <br /> <br />
                    A Cozinha República I, localizada na Rua Augusta, coração de São Paulo, é equipada com todos os equipamentos necessários para preparar suas receitas e impulsionar suas vendas.
                    <br />
                    <br />
                    Equipamentos:
                    <ol>
                        <li>Bancadas e prateleiras de inox</li>
                        <li>Fogão industrial</li>
                        <li>Geçadeiras e freezes comerciais</li>
                        <li>Coifa e sistema de exaustão</li>
                        <li>Pia com acionamento não manual</li>
                    </ol>
                </div>
                
                <div>
                    <br />
                    <Calendario/><br />

                    <NavLink to='/AgdBancada'>
                        <NextBtn text="Confirmar"/>
                    </NavLink>
                </div>
            </div>
        </>
    )
}