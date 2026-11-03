import { HeartIcon } from '@phosphor-icons/react'
import './RestaurantCard.css'
import { useState } from 'react'
export const RestaurantCard=({restaurantName,tag1,tag2})=>{

    const [FavToggle, setFavToggle]=useState(false)

    return(
        <div className='restaurantCard'>
            {/*Placeholder da imagem do restaurante*/}
            <div className='restaurantIcon'></div>
            <div className='restaurantInfo'>
                <p className='restaurantName'>{restaurantName}</p>
                <ul className='restaurantTags'>
                    <li>{`#${tag1}`}</li>
                    <li>{`#${tag2}`}</li>
                </ul>
            </div>
            <HeartIcon onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setFavToggle(!FavToggle);
                }} 
                className={`restaurantFavIcon ${FavToggle ? "activated" : ""}`} 
                size={24} weight='fill'/>
        </div>
    )
}
