const toggleButton = document.getElementsByClassName('toggle-button')[0]
const navigation = document.getElementsByClassName('nav__links')[0]
const login = document.getElementsByClassName('log-btn')[0]


toggleButton.addEventListener('click', () => {
    navigation.classList.toggle('active')
    login.classList.toggle('active')
})
