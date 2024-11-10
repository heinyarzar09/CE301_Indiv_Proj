document.addEventListener('DOMContentLoaded', function () {
    // Initialize GSAP animations for the navbar, main content, and footer
    gsap.from(".navbar", {
        duration: 0.8,
        y: -40,
        opacity: 0,
        ease: "power2.out"
    });

    gsap.from(".container", {
        duration: 1,
        y: 30,
        opacity: 0,
        ease: "power2.out",
        delay: 0.3
    });

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

    // THREE.js Particle Animation Setup
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
        particlePositions[i * 3] = (Math.random() - 0.5) * 20;
        particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 20;
        particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 20;
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
    document.addEventListener("DOMContentLoaded", function() {
        // Get the canvas element and set it to full screen
        const canvas = document.getElementById('particle-canvas');
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
    
        // Set up the scene, camera, and renderer
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
    
        // Create particles
        const particleCount = 500; // Reduced particle count for subtlety
        const particles = new THREE.BufferGeometry();
        const particlePositions = new Float32Array(particleCount * 3);
    
        for (let i = 0; i < particleCount; i++) {
            particlePositions[i * 3] = (Math.random() - 0.5) * 15; // X
            particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 15; // Y
            particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 15; // Z
        }
    
        particles.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    
        // Particle material
        const particleMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 0.03, // Smaller particle size for subtle effect
            transparent: true,
            opacity: 0.7 // Reduced opacity for subtlety
        });
    
        // Create particle system
        const particleSystem = new THREE.Points(particles, particleMaterial);
        scene.add(particleSystem);
    
        camera.position.z = 8; // Move the camera back for a wider view
    
        // Animation loop
        function animate() {
            requestAnimationFrame(animate);
    
            // Slow down the rotation speed for a subtle effect
            particleSystem.rotation.y += 0.0005;
    
            renderer.render(scene, camera);
        }
    
        animate();
    
        // Handle window resize
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    });
    
    camera.position.z = 8;

    function animate() {
        requestAnimationFrame(animate);
        particleSystem.rotation.y += 0.0005;
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
