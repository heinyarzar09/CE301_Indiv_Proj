document.addEventListener('DOMContentLoaded', function () {
    // ===========================
    // GSAP Animations
    // ===========================
    
    // Animate navbar
    gsap.from(".navbar", {
        duration: 0.8,
        y: -40,
        opacity: 0,
        ease: "power2.out"
    });

    // Animate main content
    gsap.from(".container", {
        duration: 1,
        y: 30,
        opacity: 0,
        ease: "power2.out",
        delay: 0.3
    });

    // Animate footer
    gsap.from("footer", {
        duration: 0.7,
        y: 20,
        opacity: 0,
        ease: "power2.out",
        delay: 0.6
    });

    // Hover animations for navbar links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', () => {
            gsap.to(link, {
                duration: 0.2,
                scale: 1.05,
                color: "#4a90e2",
                ease: "power1.out"
            });
        });
        link.addEventListener('mouseleave', () => {
            gsap.to(link, {
                duration: 0.2,
                scale: 1,
                color: "#555",
                ease: "power1.out"
            });
        });
    });

    // Smooth toggle for dropdown menus
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('click', function (event) {
            event.preventDefault();
            const dropdownMenu = this.nextElementSibling;
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                if (menu !== dropdownMenu) menu.classList.remove('show');
            });
            dropdownMenu.classList.toggle('show');
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function (event) {
        if (!event.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => menu.classList.remove('show'));
        }
    });

    // ===========================
    // THREE.js Particle Animation Setup
    // ===========================

    // Setup canvas
    const canvas = document.getElementById('particle-canvas');
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);

    // Create particles
    const particleCount = 500;
    const particles = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
        particlePositions[i * 3] = (Math.random() - 0.5) * 15;
        particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 15;
        particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 15;
    }

    particles.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));

    const particleMaterial = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 0.03,
        transparent: true,
        opacity: 0.7
    });

    const particleSystem = new THREE.Points(particles, particleMaterial);
    scene.add(particleSystem);

    // Set camera position
    camera.position.z = 8;

    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        particleSystem.rotation.y += 0.0005; // Subtle rotation
        renderer.render(scene, camera);
    }
    animate();

    // Adjust camera and renderer on window resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
});
