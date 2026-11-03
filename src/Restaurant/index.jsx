
import { Link, NavLink, useParams } from 'react-router-dom'
import { restaurantsList } from '../data/restaurantsData'
import { dishesList } from '../data/dishesData'
import { HeartIcon, StarIcon } from '@phosphor-icons/react'
import './Restaurant.css'
import { Header } from '../Components/Header'
import { CardCardapio } from '../CardCardapio'

export const Restaurant = () => {
    const { id } = useParams()
    const restaurant = restaurantsList.find(
        (item) => item.id === Number(id)
    )
    if (!restaurant) {
        return (
            <main className="restaurantPage">
                <h1>Restaurante não encontrado :/</h1>
                <Link to="/">Voltar para o início</Link>
            </main>
        )
    }
    const tags = [restaurant.tag1, restaurant.tag2].filter(Boolean)
    const menu = dishesList.filter((dish) => dish.restaurantId === restaurant.id)

    return (
        <main className="restaurantPage">
            <Header/>
           {/* Banner */}
            <section className="restaurantPageBanner h-[200px] md:h-[320px]">
                <button
                    className="restaurantPageFavorite"
                    aria-label="Adicionar aos favoritos"
                >
                    <HeartIcon weight="fill" />
                </button>
            </section>

            {/* Informações do restaurante */}
            <section className="restaurantPageInfo">
                <div className="restaurantPageLogo">
                    {/* Espaço reservado para a logo */}
                </div>

                <h1 className="restaurantPageName text-[28px] md:text-[36px]">
                    {restaurant.restaurantName}
                </h1>

                <div className="restaurantPageRating">
                    {[1, 2, 3, 4, 5].map((star) => (
                        <StarIcon key={star} weight="fill" />
                    ))}
                </div>
            </section>

            {/* Cardápio */}
            <section className="restaurantPageMenu max-w-[1390px] mx-auto px-4">
                <div className="restaurantPageGrid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 justify-items-center gap-x-[56px] gap-y-[32px] w-full mx-auto">
                    {menu.map((dish) => (
                        <NavLink key={dish.id} to={`/prato/${dish.id}`} className="block w-full">
                            <CardCardapio dishName={dish.name} description={dish.description} price={dish.price}/>
                        </NavLink>
                    ))}
                </div>
            </section>
        </main>
    )
}
