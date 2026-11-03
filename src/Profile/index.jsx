import { HeartIcon, ReceiptIcon, StarIcon } from '@phosphor-icons/react'
import { user, ordersHistory } from '../data/userData'
import { Header } from '../Components/Header'
import { OrderCard } from './OrderCard'
import './Profile.css'
export const Profile=()=>{

    const stats=[
        { id: 1, icon: <ReceiptIcon/>, value: ordersHistory.length, label: 'Pedidos realizados' },
        { id: 2, icon: <HeartIcon weight='fill'/>, value: user.favorites, label: 'Restaurantes favoritos' },
        { id: 3, icon: <StarIcon weight='fill'/>, value: user.reviews, label: 'Avaliações feitas' }
    ]

    return(
        <main className='profilePage'>
            <Header/>
            <section className='profileHero h-[120px] md:h-[160px]'></section>

            <div className='profileContent max-w-[1100px] mx-auto px-4'>
                <div className='profileHeader flex flex-col items-center gap-4 text-center md:flex-row md:items-end md:gap-8 md:text-left'>
                    {/*Placeholder da foto do usuário*/}
                    <div className='profileAvatar'></div>
                    <div className='profileInfo'>
                        <h1 className='text-[32px] md:text-[40px]'>{user.name}</h1>
                        <p>{`Data de entrada no app: ${user.joinDate}`}</p>
                    </div>
                    <button type='button' className='profileManage md:ml-auto'>Gerenciar Informações</button>
                </div>

                <div className='profileStats grid grid-cols-1 sm:grid-cols-3 gap-4'>
                    {stats.map((stat)=>(
                        <div key={stat.id} className='profileStat'>
                            <span className='profileStatIcon'>{stat.icon}</span>
                            <div>
                                <p className='profileStatValue'>{stat.value}</p>
                                <p className='profileStatLabel'>{stat.label}</p>
                            </div>
                        </div>
                    ))}
                </div>

                <section className='profileOrders'>
                    <h2 className='text-[28px] md:text-[36px]'>Histórico de pedidos</h2>
                    <div className='profileOrdersList'>
                        {ordersHistory.map((order)=>(
                            <OrderCard key={order.id} order={order}/>
                        ))}
                    </div>
                </section>
            </div>
        </main>
    )
}
