import { useEffect, useState } from 'react'
import { CaretRightIcon } from "@phosphor-icons/react"
import { Ad1 } from "../Assets/Ad1"
import { Header } from "../Components/Header"
import './Home.css'
import { RestaurantCard } from "./RestaurantCard"
import { NavLink } from "react-router-dom"
export const Home=()=>{

    const [restaurants, setRestaurants] = useState([])
    const [status, setStatus] = useState('loading')

    useEffect(() => {
        let active = true
        fetch('/api/restaurantes')
            .then(async (response) => {
                const data = await response.json()
                if (!response.ok) throw new Error(data.error?.message || 'Falha ao carregar restaurantes.')
                return data.restaurantes
            })
            .then((items) => { if (active) { setRestaurants(items); setStatus('ready') } })
            .catch(() => { if (active) setStatus('error') })
        return () => { active = false }
    }, [])

    return(
        <>  
            <Header/>
            <Ad1/>
            <div className="restaurantSec max-w-[1390px] mx-auto">
                <div className="restaurantSecP">
                    <p className="restaurantSecTitle">Restaurantes</p>
                    <NavLink to="/catalogo" className="restaurantSecSM">
                        <p>Ver mais</p>
                        <CaretRightIcon className="restaurantSecIcon"/>
                    </NavLink>
                </div>
                {status === 'loading' && <p>Carregando restaurantes…</p>}
                {status === 'error' && <p role="alert">Não foi possível carregar os restaurantes.</p>}
                {status === 'ready' && <div className="restaurantGrid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 justify-items-center gap-x-[56px] gap-y-[32px] w-full mx-auto">
                    {restaurants.map((restaurant)=>(
                        <NavLink key={restaurant.id} to={`/restaurante/${restaurant.slug || restaurant.id}`} className="block w-full">
                            <RestaurantCard id={restaurant.id} restaurantName={restaurant.nome} tag1={restaurant.categorias[0] || ''} tag2={restaurant.categorias[1] || ''} image={restaurant.imagem}/>
                        </NavLink>
                    ))}
                </div>}
            </div>
        </>
    )
}
