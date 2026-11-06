import { useEffect, useState } from 'react'
import { Link, NavLink, useParams } from 'react-router-dom'
import { HeartIcon, StarIcon } from '@phosphor-icons/react'
import './Restaurant.css'
import { Header } from '../Components/Header'
import { CardCardapio } from '../CardCardapio'
import { useFavorites } from '../favoritesContext'

export const Restaurant = () => {
    const { slug } = useParams()
    const [restaurant, setRestaurant] = useState(null)
    const [status, setStatus] = useState('loading')
    const { enabled, isFavorite, toggle } = useFavorites()
    const restaurantId = restaurant?.id
    const fav = enabled && restaurantId != null && isFavorite(restaurantId)

    useEffect(() => {
        let active = true
        fetch(`/api/restaurantes/${encodeURIComponent(slug)}`)
            .then(async (response) => {
                const data = await response.json()
                if (!response.ok) throw new Error(data.error?.message || 'Restaurante não encontrado.')
                return data.restaurante
            })
            .then((item) => { if (active) { setRestaurant(item); setStatus('ready') } })
            .catch(() => { if (active) setStatus('error') })
        return () => { active = false }
    }, [slug])

    if (status === 'loading') {
        return <main className="restaurantPage"><Header/><p>Carregando restaurante…</p></main>
    }
    if (status === 'error' || !restaurant) {
        return (
            <main className="restaurantPage">
                <Header/>
                <h1>Restaurante não encontrado :/</h1>
                <Link to="/">Voltar para o início</Link>
            </main>
        )
    }

    return (
        <main className="restaurantPage">
            <Header/>
           {/* Banner */}
            <section className="restaurantPageBanner h-[200px] md:h-[320px]">
                {enabled && (
                    <button
                        className="restaurantPageFavorite"
                        aria-pressed={fav}
                        aria-label={fav ? 'Remover dos favoritos' : 'Adicionar aos favoritos'}
                        onClick={() => toggle(restaurantId)}
                    >
                        <HeartIcon weight="fill" className={fav ? 'activated' : ''} />
                    </button>
                )}
            </section>

            {/* Informações do restaurante */}
            <section className="restaurantPageInfo">
                <div className="restaurantPageLogo" style={restaurant.imagem ? { backgroundImage: `url(${restaurant.imagem})` } : undefined}>
                    {/* Espaço reservado para a logo */}
                </div>

                <h1 className="restaurantPageName text-[28px] md:text-[36px]">
                    {restaurant.nome}
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
                    {restaurant.pratos.map((dish) => (
                        <NavLink key={dish.id} to={`/restaurante/${restaurant.slug || restaurant.id}/prato/${dish.slug || dish.id}`} className="block w-full">
                            <CardCardapio id={dish.id} dishName={dish.nome} description="" price={Number(dish.preco)} image={dish.imagem}/>
                        </NavLink>
                    ))}
                </div>
            </section>
        </main>
    )
}
