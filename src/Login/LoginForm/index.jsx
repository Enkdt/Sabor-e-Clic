import { useState } from 'react';
import { LoginImg } from '../../Assets/LoginImg';
import { SignBtn } from '../../Components/SignBtn';
import { NextBtn } from '../../Components/NextBtn';
import { LoginDivider } from '../LoginDivider';
import { Input } from '../../Components/Input';
import './LoginForm.css';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../authContext';
export const LoginForm=()=>{

    const navigate=useNavigate();
    const location = useLocation();
    const { authenticate } = useAuth();
    const [email,setEmail] = useState('');
    const [password,setPassword] = useState('');
    const [error,setError]=useState('');

    const loginLogic = async (e) => {
        e.preventDefault();
        setError('');

        try {
            await authenticate(email, password);
            const destination = location.state?.from;
            navigate(typeof destination === 'string' && destination.startsWith('/') && !destination.startsWith('//') ? destination : '/');
        } catch (error) {
            setError(error.message);
        }
    }

    const inputs=[
        {
            label:"E-mail",
            placeholder:"exemplo@email.com",
            type:"text",
            value: email,
            onChange: (e) => setEmail(e.target.value)
        },
        {
            label:"Senha",
            placeholder:"Insira a sua senha",
            type:"password",
            //Pra botar os valores como tiver do input
            value: password,
            onChange: (e) => setPassword(e.target.value)
        }
    ]

return (
    <div className="loginDiv">
        <LoginImg/>

        <div className="loginForm w-full max-w-[800px]">
            <form onSubmit={loginLogic}>
                <h1 className="loginTitle transition-all duration-500 ease text-[44px] md:text-[54px] lg:text-[64px]">Bem-Vindo de volta!</h1>

                {inputs.map((input) => (
                    <div key={input.label}>
                        <Input
                            label={input.label}
                            placeholder={input.placeholder}
                            type={input.type}
                            value={input.value}
                            onChange={input.onChange}
                            className={error ? "loginInput error" : "loginInput"}
                        />

                        <p style={{ opacity: error ? 1 : 0 }} className="loginError">
                            {error || "errorPlaceholder"}
                        </p>
                    </div>
                ))}
                <NextBtn text="Continuar"/>
                <NavLink to="/recuperar-senha">Esqueceu a senha?</NavLink>
            </form>

            <LoginDivider/>
            <NavLink to="/cadastro">
                <SignBtn text="Cadastrar-se"/>
            </NavLink>
        </div>
    </div>
);

}