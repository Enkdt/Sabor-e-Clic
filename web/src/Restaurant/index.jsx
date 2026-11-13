import { useEffect, useState } from 'react'
import { Link, NavLink, useParams } from 'react-router-dom'
import { HeartIcon, StarIcon } from '@phosphor-icons/react'
import './Restaurant.css'
import { Header } from '../Components/Header'
import { CardCardapio } from '../CardCardapio'
import { useFavorites } from '../favoritesContext'
import { initials, colorFor } from '../utils/avatarColor'

export const Restaurant = () => {
    const { slug } = useParams()
    const [restaurant, setRestaurant] = useState(null)
    const [status, setStatus] = useState('loading')
    const { enabled, isFavorite, toggle, error: favError, clearError } = useFavorites()
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
        return <main id="conteudo-principal" className="restaurantPage"><Header/><p>Carregando restaurante…</p></main>
    }
    if (status === 'error' || !restaurant) {
        return (
            <main id="conteudo-principal" className="restaurantPage">
                <Header/>
                <h1>Restaurante não encontrado :/</h1>
                <Link to="/">Voltar para o início</Link>
            </main>
        )
    }

    return (
        <main id="conteudo-principal" className="restaurantPage">
            <Header/>
           {/* Banner */}
            <section className="restaurantPageBanner h-[200px] md:h-[320px]">
                {enabled && (
                    <button
                        className="restaurantPageFavorite"
                        aria-pressed={fav}
                        aria-label={fav ? 'Remover dos favoritos' : 'Adicionar aos favoritos'}
                        onClick={() => { clearError(); toggle(restaurantId) }}
                    >
                        <HeartIcon weight="fill" className={fav ? 'activated' : ''} />
                    </button>
                )}
                {enabled && favError && (
                    <p className="restaurantPageFavError" role="alert">{favError}</p>
                )}
            </section>

            {/* Informações do restaurante */}
            <section className="restaurantPageInfo">
                <div className="restaurantPageLogo" style={restaurant.imagem ? { backgroundImage: `url(${restaurant.imagem})` } : { backgroundColor: colorFor(restaurant.nome) }}>
                    {!restaurant.imagem && <span className="restaurantPageLogoInitials">{initials(restaurant.nome)}</span>}
                </div>

                <h1 className="restaurantPageName text-[28px] md:text-[36px]">
                    {restaurant.nome}
                </h1>

                <div
                    className="restaurantPageRating"
                    aria-label={
                        restaurant.avaliacao_total > 0
                            ? `Avaliação ${restaurant.avaliacao_media} de 5, ${restaurant.avaliacao_total} ${restaurant.avaliacao_total === 1 ? 'avaliação' : 'avaliações'}`
                            : 'Sem avaliações'
                    }
                >
                    {restaurant.avaliacao_total > 0 ? (
                        <>
                            {[1, 2, 3, 4, 5].map((star) => (
                                <StarIcon
                                    key={star}
                                    weight={star <= Math.round(restaurant.avaliacao_media) ? 'fill' : 'regular'}
                                />
                            ))}
                            <span className="restaurantPageRatingValue">
                                {restaurant.avaliacao_media.toFixed(1)}
                                <span className="restaurantPageRatingCount">
                                    ({restaurant.avaliacao_total})
                                </span>
                            </span>
                        </>
                    ) : (
                        <span className="restaurantPageRatingEmpty">
                            <StarIcon weight="regular" />
                            Sem avaliações
                        </span>
                    )}
                </div>
            </section>

            {/* Cardápio */}
            <section className="restaurantPageMenu max-w-[1390px] mx-auto px-4">
                <div className="restaurantPageGrid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 justify-items-center gap-x-[56px] gap-y-[32px] w-full mx-auto">
                    {restaurant.pratos.map((dish) => (
                        <NavLink key={dish.id} to={`/restaurante/${restaurant.slug || restaurant.id}/prato/${dish.slug || dish.id}`} className="block w-full">
                            <CardCardapio id={dish.id} dishName={dish.nome} description="" price={Number(dish.preco)} image={dish.imagem} available={dish.disponivel !== false}/>
                        </NavLink>
                    ))}
                </div>
            </section>
        </main>
    )
}
