(async function () {
  const action = document.querySelector('.nav-action');
  if (!action) return;
  try {
    const response = await fetch('/djangoapp/session', {credentials: 'same-origin'});
    if (!response.ok) return;
    const user = await response.json();
    if (user.status !== 'Authenticated') return;
    const wrapper = document.createElement('span');
    const name = document.createElement('span');
    name.textContent = user.userName + ' · ';
    const button = document.createElement('button');
    button.type = 'button'; button.textContent = 'Sign out';
    button.className = 'nav-action';
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        const token = document.cookie.split('; ').find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
        const result = await fetch('/djangoapp/logout', {method: 'POST', credentials: 'same-origin', headers: {'X-CSRFToken': token}});
        if (!result.ok) throw new Error('Sign out failed. Please retry.');
        sessionStorage.removeItem('username'); window.location.assign('/');
      } catch (error) {button.disabled = false; button.textContent = error.message;}
    });
    wrapper.append(name, button); action.replaceWith(wrapper);
  } catch (_) { /* The public pages remain available if the session check fails. */ }
})();
