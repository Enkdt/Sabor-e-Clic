import { CaretRightIcon } from "@phosphor-icons/react"
import { Ad1 } from "../Assets/Ad1"
import { Banner } from "../Assets/Banner"
import './Home.css'
import { RestaurantCard } from "./RestaurantCard"
export const Home=()=>{

    const restaurantsList=[
        {restaurantName:'Pop Vegan Food', tag1:'Comida Brasileira', tag2:'Marmitas'},
        {restaurantName:'Restaurante 1', tag1:'Pizzas', tag2:''},
        {restaurantName:'Restaurante 2', tag1:'Sobremesas', tag2:'Bolos'},
        {restaurantName:'Restaurante 3', tag1:'Sobremesas', tag2:'Sorvetes'},
        {restaurantName:'Restaurante 4', tag1:'Comida Brasileira', tag2:'Nordeste'},
        {restaurantName:'Restaurante 5', tag1:'Comida Japonesa', tag2:''},
    ]

    return(
        <>  
            <Banner/>
            <Ad1/>
            <div className="restaurantSec max-w-[1390px] mx-auto">
                <div className="restaurantSecP">
                    <p className="restaurantSecTitle">Restaurantes</p>
                    <div className="restaurantSecSM">
                        <p>Ver mais</p>
                        <CaretRightIcon className="restaurantSecIcon"/>
                    </div>
                </div>
                <div className="restaurantGrid grid grid -cols-1 md:grid-cols-2 lg:grid-cols-3 justify-items-center gap-x-[56px] gap-y-[32px] w-full mx-auto">
                    {restaurantsList.map((restaurant)=>(
                        <RestaurantCard restaurantName={restaurant.restaurantName} tag1={restaurant.tag1} tag2={restaurant.tag2}/>
                    ))}
                </div>
            </div>
        </>
    )
}