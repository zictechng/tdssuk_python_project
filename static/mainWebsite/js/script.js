(function ($) {
  ("use strict");

  // loader js
  $(window).on("load", function () {
    $(".fullpage_loader").fadeOut("slow", function () {
      $(this).remove(1000);
    });
  });

  // Offcanvas menu js
  $(".offcanvas-btn").on('click', function () {
    $(".offcanvas-menu, .offcanvas-overlay").addClass("active")
  });
  $(".offcanvas-overlay, .offcasvas-close").on('click', function () {
    $(".offcanvas-menu, .offcanvas-overlay").removeClass("active")
  });

  // fixed menu js
  $(window).on("scroll", function () {
    var scroll = $(window).scrollTop();
    if (scroll < 200) {
      $("#sticky-header").removeClass("sticky-menu");
      $("#header-fixed-height").removeClass("active-height");
    } else {
      $("#sticky-header").addClass("sticky-menu");
      $("#header-fixed-height").addClass("active-height");
    }
  });

  // Header search js
  $(".header-search-btn").on('click', function () {
    $(".header-search").addClass("active")
  });
  $(".close-header-search").on('click', function () {
    $(".header-search").removeClass("active")
  });

  /* Data Background js */
  $("[data-background]").each(function () {
    $(this).css("background-image", "url(" + $(this).attr("data-background") + ")")
  })

  // Nice select js
  $(document).ready(function () {
    $('select').niceSelect();
  });

  // Banner slider js
  var swiper = new Swiper(".banner-slider", {
    slidesPerView: 1,
    spaceBetween: 0,
    speed: 1800,
    loop: true,
    pagination: {
      el: ".swiper-pagination",
      clickable: true,
    },
    autoplay: {
      delay: 4000,
      disableOnInteraction: true,
      pauseOnMouseEnter:true,
    },
    on: {
      slideChangeTransitionStart: function () {
        gsap.fromTo(
          ".swiper-slide-active .subtitle", {
            opacity: 0,
            y: 80
          }, {
            opacity: 1,
            y: 0,
            duration: 1,
            delay: 1.5,
            ease: "power2.out"
          }
        );

        gsap.fromTo(
          ".swiper-slide-active .heading-one", {
            opacity: 0,
            y: 80
          }, {
            opacity: 1,
            y: 0,
            duration: 1,
            delay: 1.8,
            ease: "power2.out"
          }
        );

        gsap.fromTo(
          ".swiper-slide-active .detais", {
            opacity: 0,
            y: 80
          }, {
            opacity: 1,
            y: 0,
            duration: 1,
            delay: 2,
            ease: "power2.out"
          }
        );

        gsap.fromTo(
          ".swiper-slide-active .banner-btn", {
            opacity: 0,
            y: 80
          }, {
            opacity: 1,
            y: 0,
            duration: 1,
            delay: 2.4,
            ease: "power2.out",
            stagger: 0.2
          }
        );

        gsap.fromTo(
          ".swiper-slide-active .banner-image", {
            opacity: 0,
            y: -100
          }, {
            opacity: 1,
            y: 0,
            duration: 1.5,
            delay: 2,
            ease: "power2.out"
          }
        );
      },
    }
  });

  // Service slider js
  var swiper = new Swiper(".service-slider", {
    slidesPerView: 3,
    spaceBetween: 24,
    speed: 1200,
    loop: true,
    navigation: {
      nextEl: ".next",
      prevEl: ".prev",
    },
    breakpoints: {
      1200: {
        slidesPerView: 3,
      },
      992: {
        slidesPerView: 2,
      },
      768: {
        slidesPerView: 2,
      },
      576: {
        slidesPerView: 1,
      },
      0: {
        slidesPerView: 1,
      },
    },
  });

  // clent slider js
  var swiper = new Swiper(".client-slider", {
    loop: true,
    freemode: true,
    slidesPerView: 'auto',
    spaceBetween: 111,
    centeredSlides: false,
    allowTouchMove: false,
    speed: 4000,
    autoplay: {
      delay: 1,
      disableOnInteraction: true,
    },
    breakpoints: {
      1400: {
        slidesPerView: 7,
      },
      1200: {
        slidesPerView: 6,
        spaceBetween: 60,
      },
      768: {
        slidesPerView: 4,
        spaceBetween: 40,
      },
      576: {
        slidesPerView: 3,
      },
      0: {
        slidesPerView: 2,
        spaceBetween: 60,
      },
    },
  });

  // testimonial slider js
  var swiper = new Swiper(".testimonial-slider", {
    slidesPerView: 1,
    loop: true,
    speed: 1200,
    navigation: {
      nextEl: ".next",
      prevEl: ".prev",
    },
  });

  // testimonial slider two js
  var swiper = new Swiper(".testimonial-slider-two", {
    slidesPerView: 3,
    spaceBetween: 24,
    speed: 1200,
    loop: true,
    autoplay: {
      delay: 2000,
      disableOnInteraction: true,
    },
    navigation: {
      nextEl: ".next",
      prevEl: ".prev",
    },
    breakpoints: {
      1200: {
        slidesPerView: 3,
      },
      992: {
        slidesPerView: 2,
      },
      768: {
        slidesPerView: 2,
      },
      576: {
        slidesPerView: 1,
      },
      0: {
        slidesPerView: 1,
      },
    },
  });

  // portfolio slider
  var swiper = new Swiper(".portfolio-slider", {
    effect: "coverflow",
    slidesPerView: 4,
    spaceBetween: 0,
    grabCursor: true,
    speed: 1500,
    loop: true,
    centeredSlides: true,
    autoplay: {
      delay: 2000,
      disableOnInteraction: true,
    },
    coverflowEffect: {
      rotate: 0,
      stretch: 0,
      depth: 100,
      modifier: 1.5,
      slideShadows: false,
    },
    breakpoints: {
      1400: {
        slidesPerView: 4,
      },
      1200: {
        slidesPerView: 4,
      },
      992: {
        slidesPerView: 3,
      },
      768: {
        slidesPerView: 2,
      },
      576: {
        slidesPerView: 1,
      },
      0: {
        slidesPerView: 1,
      },
    },
  });

  // Custom range input js
  $(document).ready(function () {
    var $elemWrapper = $(".slider-wrapper"),
      $elemRange = $("#slider-range"),
      $elemRangeVal = $("#slider-value"),
      ratio = 100 / ($elemRange.attr("max") - $elemRange.attr("min"));
    $elemRange.on("input", function () {
      var value = ratio * (this.value - $elemRange.attr("min"));
      $elemRangeVal.text(this.value);
      $elemWrapper.css("--value", value);
    });
    $elemRange.trigger("input");
  });

  // progressbar animation js
  const progressBars = document.querySelectorAll('.progress-bar');
  if (progressBars.length > 0) {
    progressBars.forEach(bar => {
      gsap.fromTo(bar, {
        width: "30%"
      }, {
        width: bar.style.width,
        scrollTrigger: {
          trigger: bar,
          start: "top 80%",
          toggleActions: "play none none none",
          once: true,
        }
      });
    });
  }

  // Brands logo js
  var brandSlider = new Swiper('.brand-logo', {
    loop: true,
    freemode: true,
    slidesPerView: 'auto',
    spaceBetween: 111,
    centeredSlides: false,
    allowTouchMove: false,
    speed: 4000,
    autoplay: {
      delay: 1,
      disableOnInteraction: true,
    },
    breakpoints: {
      '992': {
        spaceBetween: 90,
      },
      '768': {
        spaceBetween: 90,
      },
      '576': {
        spaceBetween: 90,
      },
      '0': {
        spaceBetween: 50,
      },
    }
  });

  // simpleParallax js
  var image = document.getElementsByClassName('imageParallax');

  if (image.length > 0) { // Check if the class exists
    new simpleParallax(image, {
      delay: 2,
      transition: 'cubic-bezier(0,0,0,1)',
      scale: 1.3,
    });
  }


  document.addEventListener("DOMContentLoaded", function () {
    // Split text animation
    if ($(".split-text").length > 0) {
      let st = $(".split-text");
      if (st.length == 0) return;
      gsap.registerPlugin(SplitText);
      st.each(function (index, el) {
        el.split = new SplitText(el, {
          type: "lines,words,chars",
          linesClass: "tp-split-line"
        });
        gsap.set(el, {
          perspective: 400
        });
        if ($(el).hasClass('right')) {
          gsap.set(el.split.chars, {
            opacity: 0,
            x: "50",
            ease: "Back.easeOut",
          });
        }
        if ($(el).hasClass('left')) {
          gsap.set(el.split.chars, {
            opacity: 0,
            x: "-50",
            ease: "circ.out",
          });
        }
        if ($(el).hasClass('up')) {
          gsap.set(el.split.chars, {
            opacity: 0,
            y: "80",
            ease: "circ.out",
          });
        }
        if ($(el).hasClass('down')) {
          gsap.set(el.split.chars, {
            opacity: 0,
            y: "-80",
            ease: "circ.out",
          });
        }
        el.anim = gsap.to(el.split.chars, {
          scrollTrigger: {
            trigger: el,
            start: "top 90%",
          },
          x: "0",
          y: "0",
          rotateX: "0",
          scale: 1,
          opacity: 1,
          duration: 0.6,
          stagger: 0.03,
        });
      });
    }

    // Image reveal js
    let revealContainers = document.querySelectorAll(".reveal");
    revealContainers.forEach((container) => {
      let image = container.querySelector("img");
      let tl = gsap.timeline({
        scrollTrigger: {
          trigger: container,
          toggleActions: "play none none none"
        }
      });

      tl.set(container, {
        autoAlpha: 1
      });

      if (container.classList.contains('zoom-out')) {
        // Zoom-out effect
        tl.from(image, 1.5, {
          scale: 1.4,
          ease: Power2.out
        });
      } else if (container.classList.contains('left') || container.classList.contains('right')) {
        let xPercent = container.classList.contains('left') ? -100 : 100;
        tl.from(container, 1.5, {
          xPercent,
          ease: Power2.out
        });
        tl.from(image, 1.5, {
          xPercent: -xPercent,
          scale: 1,
          delay: -1.5,
          ease: Power2.out
        });
      } else if (container.classList.contains('up') || container.classList.contains('down')) {
        let yPercent = container.classList.contains('up') ? 100 : -100;
        tl.from(container, 1.5, {
          yPercent,
          ease: Power2.out
        });
        tl.from(image, 1.5, {
          yPercent: -yPercent,
          scale: 1,
          delay: -1.5,
          ease: Power2.out
        });
      }
    });

    // Fade-up effect animation
    $(".content").each(function (i) {
      let target = $(this).find(".fade-up");

      let tl = gsap.timeline({
        scrollTrigger: {
          trigger: $(this),
          start: 'top 70%',
          toggleActions: 'play none none none',
          markers: false,
        }
      });

      if (target.length) {
        tl.from(target, {
          opacity: 0,
          y: 60,
          duration: 0.6,
          stagger: 0.2,
        });
      }
    });
  });

  // Jquery Appear raidal
  if (typeof ($.fn.knob) != 'undefined') {
    $('.knob').each(function () {
      var $this = $(this),
        knobVal = $this.attr('data-rel');

      $this.knob({
        'draw': function () {
          $(this.i).val(this.cv + '%')
        }
      });

      $this.appear(function () {
        $({
          value: 0
        }).animate({
          value: knobVal
        }, {
          duration: 2000,
          easing: 'swing',
          step: function () {
            $this.val(Math.ceil(this.value)).trigger('change');
          }
        });
      }, {
        accX: 0,
        accY: -150,
      });
    });
  }

  // portfolio tabs js
  const tabButtons = document.querySelectorAll('.portfolio-menu button[data-bs-toggle="pill"]');

  tabButtons.forEach(button => {
    button.addEventListener('shown.bs.tab', (event) => {
      const targetId = event.target.getAttribute('data-bs-target');
      const targetPane = document.querySelector(targetId);

      // Optional: Reset styles
      gsap.set(targetPane.querySelectorAll('.portfolio-item'), {
        opacity: 0,
        y: 100
      });

      // Animate in with a slight delay to ensure it's visible
      setTimeout(() => {
        gsap.to(targetPane.querySelectorAll('.portfolio-item'), {
          opacity: 1,
          y: 0,
          duration: 0.5,
          stagger: 0.1,
          ease: "power2.out"
        });
      }, 50);
    });
  });

  // price tab active on hover
  document.querySelectorAll(".feature-link").forEach((tab) => {
    tab.addEventListener("mouseover", function () {
      let tabInstance = new bootstrap.Tab(this);
      tabInstance.show();
    });
  });

  // video popup js
  $(".vidplay").magnificPopup({
    type: "iframe",
    iframe: {
      markup: '<div class="mfp-iframe-scaler">' +
        '<div class="mfp-close"></div>' +
        '<iframe class="mfp-iframe" frameborder="0" allowfullscreen></iframe>' +
        "</div>",
      patterns: {
        youtube: {
          index: "youtube.com/",
          id: "v=",
          src: "https://www.youtube.com/embed/%id%?autoplay=1",
        },
      },
      srcAction: "iframe_src",
    },
  });

  // /* Odometer Active js */
  $(".odometer").appear(function (e) {
    var odo = $(".odometer");
    odo.each(function () {
      var countNumber = $(this).attr("data-count");
      $(this).html(countNumber);
    });
  });

  // back to top js
  let btn = $(".scroll-to-top");

  $(window).scroll(function () {
    btn.toggleClass("show", $(window).scrollTop() > 300);
  });

  btn.click(function (e) {
    e.preventDefault();
    if (navigator.userAgent.toLowerCase().indexOf("firefox") > -1) {
      $("html").animate({
          scrollTop: 0,
        },
        1000
      );
    } else {
      $("html, body").animate({
          scrollTop: 0,
        },
        0
      );
    }
  });

  // Mobile menu js start
  $(".mobile-topbar .bars").on("click", function () {
    $(".mobile-menu-overlay,.mobile-menu-main").addClass("active");
    return false;
  });

  $(".close-mobile-menu,.mobile-menu-overlay").on("click", function () {
    $(".mobile-menu-overlay,.mobile-menu-main").removeClass("active");
  });

  $('.sub-mobile-menu ul').hide();
  $(".sub-mobile-menu a").on("click", function () {
    $('.sub-mobile-menu ul').not($(this).next("ul")).slideUp(300);
    $(".sub-mobile-menu a i").not($(this).find("i")).removeClass("fa-chevron-up").addClass("fa-chevron-down");
    $(this).next("ul").slideToggle(300);
    $(this).find("i").toggleClass("fa-chevron-up fa-chevron-down");
  });
})(jQuery);
