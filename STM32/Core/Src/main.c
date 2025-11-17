/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

// RGBY LED flag
static uint8_t LED_R_flag = 0, LED_G_flag = 0, LED_B_flag = 0, LED_Y_flag = 0;

// 0: 정상, 1: 비상 모드
static uint8_t emergency_flag = 0;

// 버튼 디바운스용
#define MAIN_LOCKOUT_MS 250u
static volatile uint32_t main_reenable_ms = 0;

// 비상일 때 LED 깜빡임 주기(ms)
#define EM_BLINK_MS 200u
static uint32_t em_blink_next_ms = 0;

// UART 1바이트 수신용
static uint8_t rx_ch = 0;
static char    cmd3[4];   // 4글자 + '\0'
static uint8_t cmd_idx = 0;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
static inline void apply_leds(void) {
  HAL_GPIO_WritePin(LED_R_GPIO_Port, LED_R_Pin, LED_R_flag ? GPIO_PIN_SET : GPIO_PIN_RESET);
  HAL_GPIO_WritePin(LED_G_GPIO_Port, LED_G_Pin, LED_G_flag ? GPIO_PIN_SET : GPIO_PIN_RESET);
  HAL_GPIO_WritePin(LED_B_GPIO_Port, LED_B_Pin, LED_B_flag ? GPIO_PIN_SET : GPIO_PIN_RESET);
  HAL_GPIO_WritePin(LED_Y_GPIO_Port, LED_Y_Pin, LED_Y_flag ? GPIO_PIN_SET : GPIO_PIN_RESET);
}
static inline void set_from_bits(const char *b3) {
  // 비상 모드면 서버 명령 무시
  if (emergency_flag) return;

  LED_R_flag = (strncmp(b3, "001", 3) == 0);
  LED_G_flag = (strncmp(b3, "010", 3) == 0);
  LED_B_flag = (strncmp(b3, "011", 3) == 0);
  LED_Y_flag = (strncmp(b3, "100", 3) == 0);
  apply_leds();
}

// emergency btn 동작
static void send_emergency_on(void) {
    const char *msg = "111\r\n";
    HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 10);
}

static void send_emergency_off(void) {
    const char *msg = "000\r\n";
    HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 10);
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
    if (GPIO_Pin == EM_BTN_Pin) {

        uint32_t now = HAL_GetTick();

        // 디바운스(락아웃): 250ms 안에 또 들어오면 무시
        if (main_reenable_ms && now < main_reenable_ms) {
            return;
        }
        main_reenable_ms = now + MAIN_LOCKOUT_MS;

        // 상태 토글
        emergency_flag ^= 1;   // 0->1, 1->0

        if (emergency_flag) {
            // 비상 모드 진입: 서버에 111, 깜빡임 시작
            send_emergency_on();
            // 처음 상태: 네 개 LED 모두 ON으로 시작
            LED_R_flag = LED_G_flag = LED_B_flag = LED_Y_flag = 1;
            apply_leds();
            em_blink_next_ms = now + EM_BLINK_MS;
        } else {
            // 비상 해제: 서버에 000, LED 모두 OFF
            send_emergency_off();
            LED_R_flag = LED_G_flag = LED_B_flag = LED_Y_flag = 0;
            apply_leds();
        }
    }
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART2_UART_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  HAL_UART_Receive_IT(&huart1, &rx_ch, 1);
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
	  uint32_t now = HAL_GetTick();

	  // 비상 모드일 때만 RGBY 깜빡이기
	  if (emergency_flag && now >= em_blink_next_ms) {
	      em_blink_next_ms = now + EM_BLINK_MS;

	      LED_R_flag ^= 1;
	      LED_G_flag ^= 1;
	      LED_B_flag ^= 1;
	      LED_Y_flag ^= 1;
	      apply_leds();
  	  }
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
// 3글자 씩 받는 callback
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {

        if (rx_ch == '\r' || rx_ch == '\n') {
            // 엔터로 구분하는 방식이면 여기서 처리
            if (cmd_idx == 3) {
                cmd3[3] = '\0';
                set_from_bits(cmd3);
            }
            cmd_idx = 0;
        } else {
            // 그냥 3글자 연속 받는 방식이면:
            if (cmd_idx < 3) {
                cmd3[cmd_idx++] = rx_ch;
            }
            if (cmd_idx == 3) {
                cmd3[3] = '\0';
                set_from_bits(cmd3);
                cmd_idx = 0;
            }
        }

        // 다음 1바이트 수신 재등록
        HAL_UART_Receive_IT(&huart1, &rx_ch, 1);
    }
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
