import { HeartIcon } from '@phosphor-icons/react'
import { useFavorites } from '../../favoritesContext'
import './RestaurantCard.css'
export const RestaurantCard=({id,restaurantName,tag1,tag2,image})=>{

    const { enabled, isFavorite, toggle }=useFavorites()
    const fav=enabled && isFavorite(id)

    return(
        <div className='restaurantCard'>
            <div className='restaurantIcon' style={image ? { backgroundImage: `url(${image})`, backgroundSize: 'cover', backgroundPosition: 'center' } : undefined}></div>
            <div className='restaurantInfo'>
                <p className='restaurantName'>{restaurantName}</p>
                <ul className='restaurantTags'>
                    {tag1 && <li>{`#${tag1}`}</li>}
                    {tag2 && <li>{`#${tag2}`}</li>}
                </ul>
            </div>
            {enabled && (
                <button
                    type='button'
                    className='restaurantFavBtn'
                    aria-pressed={fav}
                    aria-label={fav ? `Remover ${restaurantName} dos favoritos` : `Adicionar ${restaurantName} aos favoritos`}
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); toggle(id); }}
                >
                    <HeartIcon className={`restaurantFavIcon ${fav ? 'activated' : ''}`} size={24} weight='fill'/>
                </button>
            )}
        </div>
    )
}
