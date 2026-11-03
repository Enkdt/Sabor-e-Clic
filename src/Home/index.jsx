import { restaurantsList } from '../data/restaurantsData'
import { CaretRightIcon } from "@phosphor-icons/react"
import { Ad1 } from "../Assets/Ad1"
import { Header } from "../Components/Header"
import './Home.css'
import { RestaurantCard } from "./RestaurantCard"
import { NavLink } from "react-router-dom"
export const Home=()=>{


    return(
        <>  
            <Header/>
            <Ad1/>
            <div className="restaurantSec max-w-[1390px] mx-auto">
                <div className="restaurantSecP">
                    <p className="restaurantSecTitle">Restaurantes</p>
                    <div className="restaurantSecSM">
                        <p>Ver mais</p>
                        <CaretRightIcon className="restaurantSecIcon"/>
                    </div>
                </div>
                <div className="restaurantGrid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 justify-items-center gap-x-[56px] gap-y-[32px] w-full mx-auto">
                    {restaurantsList.map((restaurant)=>(
                        <NavLink key={restaurant.id} to={`/restaurante/${restaurant.id}`} className="block w-full">
                            <RestaurantCard restaurantName={restaurant.restaurantName} tag1={restaurant.tag1} tag2={restaurant.tag2}/>
                        </NavLink>
                    ))}
                </div>
            </div>
        </>
    )
}