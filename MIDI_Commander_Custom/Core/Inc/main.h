/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; Copyright (c) 2021 STMicroelectronics.
  * All rights reserved.</center></h2>
  *
  * This software component is licensed by ST under BSD 3-Clause license,
  * the "License"; You may not use this file except in compliance with the
  * License. You may obtain a copy of the License at:
  *                        opensource.org/licenses/BSD-3-Clause
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */
void Error(char *msg);

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LED_C_Pin GPIO_PIN_13
#define LED_C_GPIO_Port GPIOC
#define SW_B_Pin GPIO_PIN_14
#define SW_B_GPIO_Port GPIOC
#define LED_B_Pin GPIO_PIN_15
#define LED_B_GPIO_Port GPIOC
#define SW_C_Pin GPIO_PIN_0
#define SW_C_GPIO_Port GPIOA
#define SW_D_Pin GPIO_PIN_4
#define SW_D_GPIO_Port GPIOA
#define LED_D_Pin GPIO_PIN_5
#define LED_D_GPIO_Port GPIOA
#define SW_E_Pin GPIO_PIN_6
#define SW_E_GPIO_Port GPIOA
#define LED_E_Pin GPIO_PIN_1
#define LED_E_GPIO_Port GPIOB
#define LED_5_Pin GPIO_PIN_2
#define LED_5_GPIO_Port GPIOB
#define SW_5_Pin GPIO_PIN_10
#define SW_5_GPIO_Port GPIOB
#define LED_4_Pin GPIO_PIN_12
#define LED_4_GPIO_Port GPIOB
#define SW_4_Pin GPIO_PIN_13
#define SW_4_GPIO_Port GPIOB
#define LED_3_Pin GPIO_PIN_14
#define LED_3_GPIO_Port GPIOB
#define SW_3_Pin GPIO_PIN_15
#define SW_3_GPIO_Port GPIOB
#define LED_2_Pin GPIO_PIN_8
#define LED_2_GPIO_Port GPIOA
#define SW_2_Pin GPIO_PIN_10
#define SW_2_GPIO_Port GPIOA
#define SW_1_Pin GPIO_PIN_15
#define SW_1_GPIO_Port GPIOA
#define USB_ID_Pin GPIO_PIN_12
#define USB_ID_GPIO_Port GPIOC
#define LED_1_Pin GPIO_PIN_3
#define LED_1_GPIO_Port GPIOB
#define LED_A_Pin GPIO_PIN_4
#define LED_A_GPIO_Port GPIOB
#define SW_A_Pin GPIO_PIN_5
#define SW_A_GPIO_Port GPIOB
/* USER CODE BEGIN Private defines */

#define FIRMWARE_VERSION	"0.1A"

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
