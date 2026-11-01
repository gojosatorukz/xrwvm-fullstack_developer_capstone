import React, {useEffect, useState} from 'react';
import {Routes, Route, Link, useNavigate} from 'react-router-dom';
import './App.css';
import {Dealers, Dealer, PostReview} from './DealershipPages';

function csrf() {
  return document.cookie.split('; ').find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
}

export async function api(path, data) {
  const response = await fetch('/djangoapp/' + path, {
    credentials: 'same-origin',
    ...(data === undefined ? {} : {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()},
      body: JSON.stringify(data)
    })
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The request could not be completed.');
  return result;
}

function AuthForm({register, onSuccess}) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    const values = Object.fromEntries(new FormData(event.currentTarget));
    if (register && values.password !== values.confirmPassword) {
      setError('Passwords must match.'); setBusy(false); return;
    }
    delete values.confirmPassword;
    try {
      const user = await api(register ? 'register' : 'login', values);
      onSuccess(user);
      sessionStorage.setItem('username', user.userName);
      window.location.assign('/');
    } catch (err) {setError(err.message);} finally {setBusy(false);}
  }
  return <section className="auth-card">
    <p className="eyebrow">BESTCARS · YOUR NEXT CHAPTER</p>
    <h1>{register ? 'Create your account' : 'Welcome back'}</h1>
    <p>{register ? 'Join the community and share your dealership experience.' : 'Sign in to write reviews and manage your account.'}</p>
    <form onSubmit={submit}>
      {register && <div className="name-fields"><label>First name<input name="firstName" autoComplete="given-name" required maxLength="150" /></label><label>Last name<input name="lastName" autoComplete="family-name" required maxLength="150" /></label></div>}
      <label>Username<input name="userName" autoComplete="username" required maxLength="150" /></label>
      {register && <label>Email<input name="email" type="email" autoComplete="email" required /></label>}
      <label>Password<input name="password" type="password" autoComplete={register ? 'new-password' : 'current-password'} required /></label>
      {register && <><label>Confirm password<input name="confirmPassword" type="password" autoComplete="new-password" required /></label><small>Use at least 8 characters and avoid common passwords or personal information.</small></>}
      {error && <p className="error" role="alert">{error}</p>}
      <button disabled={busy} type="submit">{busy ? 'Please wait…' : register ? 'Create account' : 'Sign in'}</button>
    </form>
    <p>{register ? 'Already have an account? ' : 'New to BestCars? '}<Link to={register ? '/login' : '/register'}>{register ? 'Sign in' : 'Register'}</Link></p>
  </section>;
}

function App() {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  useEffect(() => {api('session').then(data => setUser(data.status === 'Authenticated' ? data : null)).catch(err => setError(err.message)).finally(() => setReady(true));}, []);
  async function signOut() {
    try {await api('logout', {}); setUser(null); sessionStorage.removeItem('username'); navigate('/login');}
    catch (err) {setError(err.message);}
  }
  return <><header className="site-header"><a className="brand" href="/">BestCars<span>FIND YOUR NEXT CHAPTER</span></a><nav aria-label="Main navigation"><a href="/">Home</a><a href="/about/">About</a><a href="/contact/">Contact</a><Link to="/dealers">Dealerships</Link>{user ? <><span>Hi, {user.firstName || user.userName}</span><button onClick={signOut}>Sign out</button></> : <><Link to="/login">Sign in</Link><Link to="/register">Register</Link></>}</nav></header><main>
    {error && <p role="alert" className="error">{error}</p>}
    {!ready ? <p role="status">Loading your session…</p> : <Routes>
      <Route path="/dealers" element={<Dealers />} />
      <Route path="/dealer/:id" element={<Dealer />} />
      <Route path="/postreview/:id" element={<PostReview user={user} />} />
      <Route path="/login" element={<AuthForm key="login" onSuccess={setUser} />} />
      <Route path="/register" element={<AuthForm key="register" register onSuccess={setUser} />} />
      <Route path="/account" element={<section className="auth-card"><p className="eyebrow">YOUR ACCOUNT</p><h1>{user ? `Welcome, ${user.firstName || user.userName}` : 'You are signed out'}</h1><p>{user ? `Signed in as ${user.userName}. Your session is ready.` : 'Sign in to continue.'}</p>{user ? <button onClick={signOut}>Sign out</button> : <Link to="/login">Sign in</Link>}</section>} />
    </Routes>}
  </main><footer>BestCars · A demonstration dealership application</footer></>;
}
export default App;
