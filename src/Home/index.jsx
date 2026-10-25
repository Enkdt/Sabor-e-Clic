import { Banner } from "../Assets/Banner"
import { CardCardapio } from "../CardCardapio"
import { HomeImg } from '../Assets/HomeImg'
import './Home.css'
export const Home=()=>{
    return(
        <>  
            <Banner/>
            <HomeImg/>
            <p>Restaurantes</p>
            <CardCardapio/>
        </>
    )
}